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
        self.model = genai.GenerativeModel(DEFAULT_MODEL)

    def generate_story_card(self, image_file, config: StoryConfig) -> StoryCard:
        try:
            pil_image = Image.open(image_file)
            resized_image = pil_image.copy()
            resized_image.thumbnail((320, 320))

            prompt = [
                f"""
                {config.age if config.age else 5}세 아이를 위한 동화 작가입니다.
                사진 속 사물을 의인화하여 캐릭터를 만들고 JSON으로 출력하세요.
                설정: {config.genre}, {config.purpose}, 주인공 {config.child_name}, 짝꿍 {config.partner_name}
                형식:
                {{ "character_name": "...", "character_type": "...", "magic_power": "...", "personality": "...", "dialogue": "...", "story_narration": "..." }}
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
        prompt = f"'{config.child_name}'와 '{config.partner_name}'의 동화. 제목 첫줄. 해요체.\n{scenes}"
        try: return self.model.generate_content(prompt).text
        except: return "이야기 생성 실패"

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