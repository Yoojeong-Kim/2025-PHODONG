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

# .env 로드
load_dotenv()

# 로깅
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("PhodongCore")

# 상수
DEFAULT_MODEL = "gemini-2.0-flash"
GENRE_OPTIONS = ["전래동화", "판타지", "히어로", "요정", "일상", "자동차", "공주/왕자", "추리", "우주", "로봇", "동물", "공룡"]
PURPOSE_OPTIONS = ["안전", "예절&규칙", "문화", "어휘력", "세계&다양성", "사고력", "기초과학", "자신감"]

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
        except: return None

class LLMService:
    def __init__(self, api_key=None):
        self.api_key = api_key if api_key else os.getenv("GOOGLE_API_KEY")
        if not self.api_key: raise ValueError("API Key가 없습니다.")
        genai.configure(api_key=self.api_key)

        generation_config = genai.types.GenerationConfig(
            temperature=1.0,
            response_mime_type="application/json"
        )
        self.model = genai.GenerativeModel(DEFAULT_MODEL, generation_config=generation_config)

    def generate_story_card(self, image_file, config: StoryConfig) -> StoryCard:
        try:
            pil_image = Image.open(image_file)
            resized_image = pil_image.copy()
            resized_image.thumbnail((320, 320))

            prompt = [
                f"""
                당신은 {config.age if config.age else 5}세 아이를 위한 베스트셀러 동화 작가입니다.
                사진 속 사물이나 풍경을 의인화하여 생동감 넘치는 캐릭터를 만들고, 
                마치 실제 동화책의 한 페이지를 읽는 듯한 아름답고 구체적인 문장으로 이야기를 서술하세요.

                [설정]
                - 장르: {config.genre}
                - 교육 목적: {config.purpose}
                - 주인공 이름: {config.child_name}
                - 짝꿍(친구) 이름: {config.partner_name}

                [필수 요구사항]
                1. **story_narration (상황 설명)**: 단순한 요약이 아니라, **눈앞에 그려지듯 생생하고 감성적인 서술형 문장**으로 작성하세요. (최소 2~3문장 이상)
                   - 나쁜 예: "친구가 꽃가루를 뿌려 위험을 알린다."
                   - 좋은 예: "그때였어요! 꼬마 요정 핑키가 반짝이는 날개를 파닥이며 나타났어요. '얘들아, 조심해!' 핑키는 주머니에서 황금빛 꽃가루를 후우~ 불어 친구들에게 위험을 알렸답니다."
                2. **dialogue (대사)**: 캐릭터의 성격이 드러나는 말투(해요체)를 사용하세요.
                3. **character_name**: 장르에 어울리는 기발한 이름을 지어주세요.

                [출력 형식 (JSON)]
                {{
                    "character_name": "캐릭터 이름",
                    "character_type": "원래 사물/동물",
                    "magic_power": "마법 능력",
                    "personality": "성격",
                    "dialogue": "캐릭터의 대사",
                    "story_narration": "동화책 서술형 상황 묘사 (길고 구체적으로)"
                }}
                """,
                resized_image
            ]
            
            safety = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
            
            response = self.model.generate_content(prompt, generation_config=genai.types.GenerationConfig(response_mime_type="application/json"), safety_settings=safety)
            
            if response.text:
                data = json.loads(Utils.clean_json_text(response.text))
                if isinstance(data, list):
                    if len(data) > 0:
                        data = data[0]
                    else:
                        data = {} # 빈 리스트가 올 경우 대비
                return StoryCard(
                    character_name=data.get("character_name", "친구"),
                    character_type=data.get("character_type", "요정"),
                    personality=data.get("personality", "밝음"),
                    magic_power=data.get("magic_power", "꿈꾸기"),
                    story_narration=data.get("story_narration", "새로운 친구를 만났어요."),
                    dialogue=data.get("dialogue", "안녕! 우리 같이 놀자."),
                    image_key=f"img_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                )
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return StoryCard(character_name="오류 요정", story_narration="잠시 연결이 불안정했어요.", dialogue="다시 시도해볼까?", image_key=f"err_{datetime.now().strftime('%Y%m%d%H%M%S%f')}")
        return StoryCard()

    def generate_final_story(self, cards: List[StoryCard], config: StoryConfig) -> str:
        scenes = "\n".join([f"- {c.character_name}: \"{c.dialogue}\" ({c.story_narration})" for c in cards])

        prompt = f"""
        당신은 세계적인 동화 작가입니다. 
        아래의 장면 조각들을 모아 '{config.child_name}'와 '{config.partner_name}'가 주인공인 하나의 완벽하고 아름다운 동화를 완성하세요.

        [조건]
        1. **제목**: 첫 줄에 창의적인 제목을 적어주세요.
        2. **문체**: 아이에게 읽어주는 듯한 다정하고 부드러운 '해요체'를 사용하세요.
        3. **구성**: 기승전결이 자연스럽게 이어지도록 장면 사이의 연결 문장을 풍부하게 추가하세요.
        4. **분량**: 각 장면의 묘사를 살려 충분히 길고 풍성하게 작성하세요.

        [장면 내용]
        {scenes}
        """

        try: return self.model.generate_content(prompt).text
        except: return "이야기 생성에 실패했어요"

class AudioService:
    @staticmethod
    def create(text: str) -> Optional[bytes]:
        try:
            clean = re.sub(r"[\*\#]", "", text)
            tts = gTTS(text=clean[:5000], lang='ko', slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except: return None