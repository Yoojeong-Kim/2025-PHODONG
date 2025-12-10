import os
import json
import io
import re
import logging
import base64
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

import google.generativeai as genai
from gtts import gTTS
from PIL import Image
from dotenv import load_dotenv

# .env 파일 로드 (로컬 환경용)
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("PhodongCore")

# 상수
DEFAULT_MODEL = "gemini-1.5-flash" # 최신 모델 권장
GENRE_OPTIONS = [
    "전래동화", "판타지", "히어로", "요정",
    "일상", "자동차", "공주/왕자", "추리",
    "우주", "로봇", "동물", "공룡",
]
PURPOSE_OPTIONS = [
    "안전", "예절&규칙", "문화",
    "어휘력", "세계&다양성", "사고력", "기초과학", "자신감",
]

@dataclass
class StoryConfig:
    child_name: str = "" 
    partner_name: str = ""
    age: str = "" 
    genre: str = GENRE_OPTIONS[0]
    purpose: str = PURPOSE_OPTIONS[0]

@dataclass
class StoryCard:
    character_name: str = "알 수 없음"
    character_type: str = "-"
    personality: str = "-"
    magic_power: str = "-"
    story_narration: str = ""
    dialogue: str = ""
    image_key: Optional[str] = None 

class Utils:
    @staticmethod
    def clean_json_text(text):
        """LLM 응답에서 JSON만 추출."""
        text = text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.startswith("```"): text = text[:text.rfind("```")]
        return text.strip()

    @staticmethod
    def get_image_base64(pil_image: Image.Image) -> Optional[str]:
        if not pil_image: return None
        try:
            buffered = io.BytesIO()
            pil_image.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode("ascii")
        except: 
            return None

class LLMService:
    def __init__(self, api_key=None):
        # API 키 우선순위: 1. 파라미터 전달 2. 환경변수(.env)
        self.api_key = api_key if api_key else os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("API Key가 없습니다. .env 파일을 확인하거나 Streamlit Secrets를 설정하세요.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(DEFAULT_MODEL)

    def build_korean_fairy_tale_prompt(self, config: StoryConfig, pil_image: Image.Image):
        child_name = config.child_name if config.child_name else "아이"
        partner_name = config.partner_name if config.partner_name else "친구"
        
        raw_age = config.age.strip()
        age_for_llm = 5 
        if raw_age.isdigit():
            age_num = int(raw_age)
            if 1 <= age_num <= 10: age_for_llm = age_num

        resized_image = pil_image.copy()
        resized_image.thumbnail((320, 320))

        prompt = [
            f"""
            당신은 {age_for_llm}세 아이를 위한 창의적인 동화 작가입니다.
            카메라 속 사물을 '살아있는 캐릭터'로 만들어 주인공({child_name})에게 말을 걸어주세요.

            ### 🎭 캐릭터 설정
            1. **이름:** {config.genre} 장르에 어울리는 기발한 이름
            2. **능력:** 사물의 마법 능력
            3. **성격:** 사물에 어울리는 성격

            ### 🗣️ 대사 및 지문
            - **대사:** 주인공이나 짝꿍({partner_name})에게 건네는 말. {config.purpose}와 관련된 내용 포함.
            - **지문:** 상황 묘사.

            ### 미션
            사진 내용과 무관하게라도 무조건 매력적인 캐릭터를 만드세요.
            결과는 JSON 형식으로만 출력하세요:
            {{
                "character_name": "...",
                "character_type": "...",
                "magic_power": "...",
                "personality": "...",
                "dialogue": "...",
                "story_narration": "..."
            }}
            """,
            resized_image
        ]
        return prompt

    def generate_story_card(self, image_file, config: StoryConfig) -> StoryCard:
        try:
            pil_image = Image.open(image_file)
            prompt = self.build_korean_fairy_tale_prompt(config, pil_image)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(response_mime_type="application/json")
            )
            
            if response.text:
                data = json.loads(Utils.clean_json_text(response.text))
                return StoryCard(
                    character_name=data.get("character_name", "사진 속 친구"),
                    character_type=data.get("character_type", "신비한 사물"),
                    personality=data.get("personality", "알 수 없음"),
                    magic_power=data.get("magic_power", "숨겨진 마법"),
                    story_narration=data.get("story_narration", "새로운 친구를 만났어요."),
                    dialogue=data.get("dialogue", "안녕! 반가워."),
                    image_key=f"img_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                )
        except Exception as e:
            logger.error(f"LLM Error: {e}")

            # 👇 [추가] 이 줄을 추가해서 화면에 에러를 띄워보세요 (테스트용)
            import streamlit as st
            st.error(f"⚠️ 실제 오류 내용: {e}")

            return StoryCard(
                character_name="신비한 친구",
                character_type="오류 요정",
                dialogue="잠시 연결이 불안정했지만, 우리는 계속 모험할 수 있어!",
                story_narration="마법의 연결이 잠시 흔들렸어요.",
                image_key=f"img_err_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            )
        return StoryCard()

    def generate_final_story(self, cards: List[StoryCard], config: StoryConfig) -> str:
        child_name = config.child_name or "아이"
        partner_name = config.partner_name or "친구"
        
        scenes = "\n".join([f"- {c.character_name}: \"{c.dialogue}\" ({c.story_narration})" for c in cards])
        prompt = f"""
        전문 동화 작가로서 '{child_name}'와 '{partner_name}'의 한국어 동화를 작성하세요.
        [조건]
        1. 첫 줄은 제목만 작성.
        2. 아이에게 읽어주는 따뜻한 '해요체'.
        3. 아래 내용을 자연스럽게 연결:
        {scenes}
        """
        try: return self.model.generate_content(prompt).text
        except Exception as e: return f"Error: {e}"

class AudioService:
    @staticmethod
    def create(text: str) -> Optional[bytes]:
        try:
            clean = re.sub(r"[\*\#]", "", text)
            lines = [l.strip() for l in clean.splitlines() if l.strip()]
            final = " ".join(lines)[:5000]
            tts = gTTS(text=final, lang='ko', slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except: return None
