import streamlit as st
import os
import json
import io
import logging
import base64
from dataclasses import dataclass, field
from typing import Optional, List
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS

# styles.py 임포트 (디자인 시스템)
import styles

# ==============================================================================
# 1. ⚙️ 설정 및 상태 관리
# ==============================================================================
load_dotenv()

st.set_page_config(
    page_title="포동 PHODONG",
    page_icon="🧸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("PhodongApp")

# [모델 설정]
# 텍스트/스토리용 (최신 모델)
TEXT_MODEL_NAME = "gemini-2.5-flash"
# 이미지 생성용 (사용자 리스트에 있던 모델)
IMAGE_MODEL_NAME = "gemini-2.0-flash-exp-image-generation"

GENRE_OPTIONS = ["전래동화", "판타지", "히어로", "요정", "일상", "자동차", "공주/왕자", "추리", "우주", "로봇", "동물", "공룡"]
PURPOSE_OPTIONS = ["안전 교육", "예절&규칙", "생활 습관", "어휘력 향상", "세계&다양성", "창의력/사고력", "기초과학", "자존감 높이기"]

# ==============================================================================
# 2. 📦 데이터 구조
# ==============================================================================
@dataclass
class StoryConfig:
    child_name: str = ""
    partner_name: str = ""
    age: int = 5
    genre: str = GENRE_OPTIONS[0]
    purpose: str = PURPOSE_OPTIONS[0]

@dataclass
class StoryCard:
    page_number: int = 0 # 0이면 표지
    character_name: str = ""
    current_object: str = "" 
    story_narration: str = ""
    dialogue: str = ""
    image: Optional[Image.Image] = None 
    audio_data: Optional[bytes] = None
    is_cover: bool = False # 표지 여부

# ==============================================================================
# 3. 🧠 AI 서비스
# ==============================================================================
class Utils:
    @staticmethod
    def clean_json_text(text):
        text = text.strip()
        if text.startswith("```json"): text = text[7:]
        elif text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        return text.strip()

    @staticmethod
    def image_to_base64(image: Image.Image) -> str:
        """PIL 이미지를 HTML 임베딩용 base64 문자열로 변환"""
        if image is None: return ""
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode()

class PhodongService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            st.error("🚨 API Key가 없습니다. .env 파일을 확인해주세요.")
            st.stop()
        
        genai.configure(api_key=self.api_key)
        self.text_model = genai.GenerativeModel(TEXT_MODEL_NAME)
        self.image_model = genai.GenerativeModel(IMAGE_MODEL_NAME)

    def analyze_image(self, image: Image.Image) -> str:
        """이미지 내용 분석"""
        try:
            res = self.text_model.generate_content(["이 사진에 있는 주요 사물이나 캐릭터가 무엇인지 단답형 한글로 알려줘.", image])
            return res.text.strip()
        except:
            return "알 수 없는 물건"

    def generate_cover_info(self, objects: List[str], config: StoryConfig) -> dict:
        """[표지 생성 1단계] 제목과 표지 그림 프롬프트 생성"""
        obj_str = ", ".join(objects)
        prompt = f"""
        동화 작가로서 다음 요소들을 포함하는 동화책의 '제목'과 '표지 그림 묘사'를 작성하세요.
        - 등장 사물들: {obj_str}
        - 장르: {config.genre}
        - 독자: {config.child_name} ({config.age}세)
        
        [출력 JSON]
        {{
            "title": "동화책 제목 (창의적이고 재미있게)",
            "cover_prompt": "표지 그림을 생성하기 위한 영어 프롬프트 (Cute, 3D render style, warm colors, etc...)"
        }}
        """
        try:
            res = self.text_model.generate_content(prompt)
            return json.loads(Utils.clean_json_text(res.text))
        except:
            return {"title": f"{config.child_name}의 신나는 모험", "cover_prompt": "Cute teddy bear adventure, 3d render style"}

    def generate_cover_image(self, prompt: str) -> Optional[Image.Image]:
        """[표지 생성 2단계] AI 이미지 생성"""
        try:
            # 이미지 생성 모델 호출
            response = self.image_model.generate_content(prompt)
            
            # 응답에서 이미지 추출 (Gemini 2.0 Flash Image Gen 방식)
            if response.parts:
                return Image.open(io.BytesIO(response.parts[0].inline_data.data))
            return None
        except Exception as e:
            logger.error(f"Image Gen Error: {e}")
            return None

    def create_character(self, object_desc: str, config: StoryConfig) -> dict:
        """주인공 캐릭터 설정"""
        prompt = f"""
        '{object_desc}' 사진을 보고 주인공 캐릭터를 설정해주세요.
        - 독자: {config.age}세, 장르: {config.genre}, 목표: {config.purpose}
        [출력 JSON] {{"name": "이름", "personality": "성격", "power": "능력"}}
        """
        try:
            res = self.text_model.generate_content(prompt)
            return json.loads(Utils.clean_json_text(res.text))
        except:
            return {"name": "포동이", "personality": "용감함", "power": "상상력"}

    def generate_page(self, page_num: int, total_pages: int, current_img_desc: str, 
                      character_info: dict, context_so_far: str, config: StoryConfig) -> dict:
        """페이지 내용 생성"""
        if page_num == 1:
            context_prompt = "이야기의 시작입니다. 주인공을 소개하고 모험을 시작하세요."
        else:
            context_prompt = f"[이전 줄거리]: {context_so_far}\n[현재 상황]: 주인공이 '{current_img_desc}'(을)를 만났습니다. 자연스럽게 이어주세요."

        final_prompt = f"""
        총 {total_pages}페이지 중 {page_num}페이지입니다.
        - 주인공: {character_info['name']}
        - 설정: {config.genre}, {config.purpose}
        - 조건: {config.age}세 아이를 위한 해요체. 지문 3~4문장, 대사 1~2문장.
        {context_prompt}
        [출력 JSON] {{"story_narration": "...", "dialogue": "..."}}
        """
        try:
            res = self.text_model.generate_content(final_prompt)
            return json.loads(Utils.clean_json_text(res.text))
        except:
            return {"story_narration": "이야기를 잇는 중 오류가 났어요.", "dialogue": "..."}

    def text_to_speech(self, text: str) -> Optional[bytes]:
        try:
            if not text: return None
            tts = gTTS(text=text, lang='ko')
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            return mp3_fp.getvalue()
        except:
            return None

    def create_download_html(self, pages: List[StoryCard], config: StoryConfig, title: str) -> str:
        """전체 동화를 하나의 HTML 파일로 변환 (이미지 포함)"""
        html_content = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                @import url('[https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&display=swap](https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&display=swap)');
                body {{ font-family: 'Gowun Dodum', sans-serif; background-color: #FFFBF8; padding: 20px; text-align: center; }}
                .book-title {{ font-family: 'Jua'; font-size: 2.5em; color: #FF9EAA; margin-bottom: 10px; }}
                .page-card {{ background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 40px; border: 1px solid #EEE; }}
                .page-img {{ width: 100%; max-width: 500px; border-radius: 10px; margin-bottom: 20px; border: 5px solid white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .narration {{ font-size: 1.1em; line-height: 1.6; color: #555; margin-bottom: 15px; text-align: left; }}
                .dialogue {{ background-color: #FFFBE6; padding: 15px; border-radius: 15px; font-family: 'Jua'; font-size: 1.3em; color: #5D4037; }}
                .footer {{ margin-top: 50px; color: #AAA; font-size: 0.8em; }}
            </style>
        </head>
        <body>
            <div class="book-title">{title}</div>
            <div style="margin-bottom:30px; color:#888;">지은이: 포동이와 {config.child_name}</div>
        """
        
        for page in pages:
            img_b64 = Utils.image_to_base64(page.image)
            html_content += f"""
            <div class="page-card">
                <img src="data:image/jpeg;base64,{img_b64}" class="page-img">
                <div class="narration">{page.story_narration}</div>
                <div class="dialogue">"{page.dialogue}"</div>
            </div>
            """
            
        html_content += """
            <div class="footer">- The End -<br>Created by PHODONG</div>
        </body></html>
        """
        return html_content

# ==============================================================================
# 4. 🖥️ UI / VIEW LAYER
# ==============================================================================

def init_session_state():
    if "book_pages" not in st.session_state:
        st.session_state.book_pages = []
    if "book_title" not in st.session_state:
        st.session_state.book_title = "나만의 동화책"
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "single" # single(한장씩) or all(전체보기)

def render_all_pages_view(config: StoryConfig):
    """[추가된 기능] 전체 페이지 이어보기 및 저장"""
    st.markdown(f"<h2 class='font-heading' style='text-align:center; color:#FF9EAA;'>📘 {st.session_state.book_title}</h2>", unsafe_allow_html=True)
    st.caption("아래로 스크롤하여 전체 이야기를 읽어보세요!")

    pages = st.session_state.book_pages
    service = PhodongService() # for download generation

    # 전체 페이지 렌더링
    for page in pages:
        with st.container():
            st.markdown(f"""
            <div class='content-box' style='margin-bottom: 30px;'>
                <div style='text-align:center; margin-bottom:10px; font-family:Jua; color:#A0C4FF;'>
                    {'🧸 표지' if page.is_cover else f'Page {page.page_number}'}
                </div>
            """, unsafe_allow_html=True)
            
            st.image(page.image, use_container_width=True)
            
            st.markdown(f"""
                <div style='margin-top:20px; font-size:1.1rem; line-height:1.6;'>
                    {page.story_narration}
                </div>
                <div class='dialogue-box' style='margin-top:15px; margin-bottom:0;'>
                    <div class='dialogue-text'>"{page.dialogue}"</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # 다운로드 버튼 영역
    st.divider()
    st.markdown("<h3 class='font-heading'>💾 동화책 소장하기</h3>", unsafe_allow_html=True)
    
    html_data = service.create_download_html(pages, config, st.session_state.book_title)
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button(
            label="📘 동화책 다운로드 (HTML)",
            data=html_data,
            file_name=f"{config.child_name}_story.html",
            mime="text/html",
            use_container_width=True,
            type="primary"
        )
    with col_d2:
        if st.button("🔄 처음으로 돌아가기", use_container_width=True):
            st.session_state.book_pages = []
            st.rerun()

def main():
    styles.DesignSystem.inject_css()
    init_session_state()
    service = PhodongService()

    # --- 헤더 ---
    st.markdown("""
        <div class="landing-hero" style="text-align:center; padding-bottom: 20px;">
            <h1 class="landing-title">나만의 동화책 만들기</h1>
            <p class="landing-subtitle">사진을 올리면 <b>포동이</b>가 이야기를 만들어줘요!</p>
        </div>
    """, unsafe_allow_html=True)

    # --- 메인 로직 ---
    # Case 1: 책이 아직 없음 -> 입력 폼 표시
    if not st.session_state.book_pages:
        left_col, right_col = st.columns([1, 1], gap="large")

        with left_col:
            with st.expander("🧸 어떻게 만드나요? (사용법 보기)", expanded=True):
                folder = styles.ArtWork.get_folder(40)
                bear_icon = styles.ArtWork.get_bear(40)
                book = styles.ArtWork.get_book_cover(40)
                st.markdown(styles.Utils.clean_html(f"""
                    <div class="step-container">
                        <div class="step-item step-1">
                            <div>{folder}</div>
                            <div class="step-title" style="color:#A0C4FF;">1. 사진 선택</div>
                            <div class="step-desc">3~5장의 사진을 골라주세요.</div>
                        </div>
                        <div class="step-item step-2">
                            <div>{bear_icon}</div>
                            <div class="step-title" style="color:#FFD580;">2. AI 창작</div>
                            <div class="step-desc">표지 그림과 이야기를 지어줘요.</div>
                        </div>
                        <div class="step-item step-3">
                            <div>{book}</div>
                            <div class="step-title" style="color:#FF9EAA;">3. 책 완성</div>
                            <div class="step-desc">전체 내용을 저장할 수 있어요.</div>
                        </div>
                    </div>
                """), unsafe_allow_html=True)

        with right_col:
            st.markdown(styles.Utils.clean_html("""<div class="landing-action"><div class="action-header">👇 이야기 설정 & 사진 업로드</div>"""), unsafe_allow_html=True)
            
            c_in1, c_in2 = st.columns(2)
            with c_in1: child_name = st.text_input("아이 이름", value="포동이")
            with c_in2: age = st.slider("아이 연령", 3, 9, 5)
            partner_name = st.text_input("함께하는 어른", value="엄마")
            
            c_sel1, c_sel2 = st.columns(2)
            with c_sel1: genre = st.selectbox("장르", GENRE_OPTIONS)
            with c_sel2: purpose = st.selectbox("교육 목표", PURPOSE_OPTIONS)
            
            st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
            
            uploaded_files = st.file_uploader(
                "사진을 순서대로 여러 장 올려주세요! (최대 5장)", 
                type=["jpg", "png", "jpeg"], 
                accept_multiple_files=True,
                label_visibility="collapsed"
            )
            
            process_btn = st.button("✨ 동화책 만들기 시작!", type="primary", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if process_btn:
                if uploaded_files:
                    config = StoryConfig(child_name, partner_name, age, genre, purpose)
                    total_files = len(uploaded_files)
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    temp_book = []
                    context_so_far = "" 
                    character_info = {}
                    
                    try:
                        # 1. 전체 사진 분석 (표지 생성을 위해)
                        status_text.markdown("🎨 **동화책 표지를 그리고 있어요...** (잠시만 기다려주세요!)")
                        all_images = [Image.open(f) for f in uploaded_files]
                        
                        # [표지 생성]
                        # 1-1. 각 사진의 핵심 사물 파악
                        obj_list = []
                        for img in all_images[:3]: # 너무 많으면 오래 걸리니 앞 3장만
                            obj_list.append(service.analyze_image(img))
                        
                        # 1-2. 제목 및 표지 프롬프트 생성
                        cover_info = service.generate_cover_info(obj_list, config)
                        st.session_state.book_title = cover_info.get("title", "나만의 동화책")
                        
                        # 1-3. 표지 이미지 생성 (AI Image Gen)
                        cover_img = service.generate_cover_image(cover_info.get("cover_prompt", ""))
                        
                        # 표지 카드 저장
                        if cover_img:
                            cover_card = StoryCard(
                                page_number=0,
                                character_name="표지",
                                story_narration=f"제목: {st.session_state.book_title}",
                                dialogue=f"지은이: 포동이와 {child_name}",
                                image=cover_img,
                                is_cover=True
                            )
                            temp_book.append(cover_card)

                        # [본문 생성]
                        for i, image in enumerate(all_images):
                            current_page = i + 1
                            status_text.markdown(f"**📖 {current_page}번째 페이지 만드는 중...** ({current_page}/{total_files})")
                            
                            # 사물 인식 (이미 위에서 했지만 정확도를 위해 개별 재호출 or 리스트 활용)
                            obj_desc = obj_list[i] if i < len(obj_list) else service.analyze_image(image)
                            
                            if i == 0:
                                character_info = service.create_character(obj_desc, config)
                            
                            page_data = service.generate_page(
                                page_num=current_page,
                                total_pages=total_files,
                                current_img_desc=obj_desc,
                                character_info=character_info,
                                context_so_far=context_so_far,
                                config=config
                            )
                            
                            audio = service.text_to_speech(page_data['dialogue'])
                            
                            card = StoryCard(
                                page_number=current_page,
                                character_name=character_info.get('name', child_name),
                                current_object=obj_desc,
                                story_narration=page_data['story_narration'],
                                dialogue=page_data['dialogue'],
                                image=image,
                                audio_data=audio
                            )
                            temp_book.append(card)
                            context_so_far += f"\n[Page {current_page}] {page_data['story_narration']}"
                            progress_bar.progress((i + 1) / total_files)
                        
                        st.session_state.book_pages = temp_book
                        st.session_state.config = config
                        st.rerun()

                    except Exception as e:
                        st.error(f"에러 발생: {e}")
                else:
                    st.warning("사진을 최소 1장 이상 올려주세요!")

    # Case 2: 책 완성 -> 전체 보기 모드
    else:
        if "config" in st.session_state:
            render_all_pages_view(st.session_state.config)

if __name__ == "__main__":
    main()import streamlit as st
import os
import json
import io
import logging
import base64
from dataclasses import dataclass, field
from typing import Optional, List
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS

# styles.py 임포트 (디자인 시스템)
import styles

# ==============================================================================
# 1. ⚙️ 설정 및 상태 관리
# ==============================================================================
load_dotenv()

st.set_page_config(
    page_title="포동 PHODONG",
    page_icon="🧸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("PhodongApp")

# [모델 설정]
# 텍스트/스토리용 (최신 모델)
TEXT_MODEL_NAME = "gemini-2.5-flash"
# 이미지 생성용 (사용자 리스트에 있던 모델)
IMAGE_MODEL_NAME = "gemini-2.0-flash-exp-image-generation"

GENRE_OPTIONS = ["전래동화", "판타지", "히어로", "요정", "일상", "자동차", "공주/왕자", "추리", "우주", "로봇", "동물", "공룡"]
PURPOSE_OPTIONS = ["안전 교육", "예절&규칙", "생활 습관", "어휘력 향상", "세계&다양성", "창의력/사고력", "기초과학", "자존감 높이기"]

# ==============================================================================
# 2. 📦 데이터 구조
# ==============================================================================
@dataclass
class StoryConfig:
    child_name: str = ""
    partner_name: str = ""
    age: int = 5
    genre: str = GENRE_OPTIONS[0]
    purpose: str = PURPOSE_OPTIONS[0]

@dataclass
class StoryCard:
    page_number: int = 0 # 0이면 표지
    character_name: str = ""
    current_object: str = "" 
    story_narration: str = ""
    dialogue: str = ""
    image: Optional[Image.Image] = None 
    audio_data: Optional[bytes] = None
    is_cover: bool = False # 표지 여부

# ==============================================================================
# 3. 🧠 AI 서비스
# ==============================================================================
class Utils:
    @staticmethod
    def clean_json_text(text):
        text = text.strip()
        if text.startswith("```json"): text = text[7:]
        elif text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        return text.strip()

    @staticmethod
    def image_to_base64(image: Image.Image) -> str:
        """PIL 이미지를 HTML 임베딩용 base64 문자열로 변환"""
        if image is None: return ""
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode()

class PhodongService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            st.error("🚨 API Key가 없습니다. .env 파일을 확인해주세요.")
            st.stop()
        
        genai.configure(api_key=self.api_key)
        self.text_model = genai.GenerativeModel(TEXT_MODEL_NAME)
        self.image_model = genai.GenerativeModel(IMAGE_MODEL_NAME)

    def analyze_image(self, image: Image.Image) -> str:
        """이미지 내용 분석"""
        try:
            res = self.text_model.generate_content(["이 사진에 있는 주요 사물이나 캐릭터가 무엇인지 단답형 한글로 알려줘.", image])
            return res.text.strip()
        except:
            return "알 수 없는 물건"

    def generate_cover_info(self, objects: List[str], config: StoryConfig) -> dict:
        """[표지 생성 1단계] 제목과 표지 그림 프롬프트 생성"""
        obj_str = ", ".join(objects)
        prompt = f"""
        동화 작가로서 다음 요소들을 포함하는 동화책의 '제목'과 '표지 그림 묘사'를 작성하세요.
        - 등장 사물들: {obj_str}
        - 장르: {config.genre}
        - 독자: {config.child_name} ({config.age}세)
        
        [출력 JSON]
        {{
            "title": "동화책 제목 (창의적이고 재미있게)",
            "cover_prompt": "표지 그림을 생성하기 위한 영어 프롬프트 (Cute, 3D render style, warm colors, etc...)"
        }}
        """
        try:
            res = self.text_model.generate_content(prompt)
            return json.loads(Utils.clean_json_text(res.text))
        except:
            return {"title": f"{config.child_name}의 신나는 모험", "cover_prompt": "Cute teddy bear adventure, 3d render style"}

    def generate_cover_image(self, prompt: str) -> Optional[Image.Image]:
        """[표지 생성 2단계] AI 이미지 생성"""
        try:
            # 이미지 생성 모델 호출
            response = self.image_model.generate_content(prompt)
            
            # 응답에서 이미지 추출 (Gemini 2.0 Flash Image Gen 방식)
            if response.parts:
                return Image.open(io.BytesIO(response.parts[0].inline_data.data))
            return None
        except Exception as e:
            logger.error(f"Image Gen Error: {e}")
            return None

    def create_character(self, object_desc: str, config: StoryConfig) -> dict:
        """주인공 캐릭터 설정"""
        prompt = f"""
        '{object_desc}' 사진을 보고 주인공 캐릭터를 설정해주세요.
        - 독자: {config.age}세, 장르: {config.genre}, 목표: {config.purpose}
        [출력 JSON] {{"name": "이름", "personality": "성격", "power": "능력"}}
        """
        try:
            res = self.text_model.generate_content(prompt)
            return json.loads(Utils.clean_json_text(res.text))
        except:
            return {"name": "포동이", "personality": "용감함", "power": "상상력"}

    def generate_page(self, page_num: int, total_pages: int, current_img_desc: str, 
                      character_info: dict, context_so_far: str, config: StoryConfig) -> dict:
        """페이지 내용 생성"""
        if page_num == 1:
            context_prompt = "이야기의 시작입니다. 주인공을 소개하고 모험을 시작하세요."
        else:
            context_prompt = f"[이전 줄거리]: {context_so_far}\n[현재 상황]: 주인공이 '{current_img_desc}'(을)를 만났습니다. 자연스럽게 이어주세요."

        final_prompt = f"""
        총 {total_pages}페이지 중 {page_num}페이지입니다.
        - 주인공: {character_info['name']}
        - 설정: {config.genre}, {config.purpose}
        - 조건: {config.age}세 아이를 위한 해요체. 지문 3~4문장, 대사 1~2문장.
        {context_prompt}
        [출력 JSON] {{"story_narration": "...", "dialogue": "..."}}
        """
        try:
            res = self.text_model.generate_content(final_prompt)
            return json.loads(Utils.clean_json_text(res.text))
        except:
            return {"story_narration": "이야기를 잇는 중 오류가 났어요.", "dialogue": "..."}

    def text_to_speech(self, text: str) -> Optional[bytes]:
        try:
            if not text: return None
            tts = gTTS(text=text, lang='ko')
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            return mp3_fp.getvalue()
        except:
            return None

    def create_download_html(self, pages: List[StoryCard], config: StoryConfig, title: str) -> str:
        """전체 동화를 하나의 HTML 파일로 변환 (이미지 포함)"""
        html_content = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                @import url('[https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&display=swap](https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&display=swap)');
                body {{ font-family: 'Gowun Dodum', sans-serif; background-color: #FFFBF8; padding: 20px; text-align: center; }}
                .book-title {{ font-family: 'Jua'; font-size: 2.5em; color: #FF9EAA; margin-bottom: 10px; }}
                .page-card {{ background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 40px; border: 1px solid #EEE; }}
                .page-img {{ width: 100%; max-width: 500px; border-radius: 10px; margin-bottom: 20px; border: 5px solid white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .narration {{ font-size: 1.1em; line-height: 1.6; color: #555; margin-bottom: 15px; text-align: left; }}
                .dialogue {{ background-color: #FFFBE6; padding: 15px; border-radius: 15px; font-family: 'Jua'; font-size: 1.3em; color: #5D4037; }}
                .footer {{ margin-top: 50px; color: #AAA; font-size: 0.8em; }}
            </style>
        </head>
        <body>
            <div class="book-title">{title}</div>
            <div style="margin-bottom:30px; color:#888;">지은이: 포동이와 {config.child_name}</div>
        """
        
        for page in pages:
            img_b64 = Utils.image_to_base64(page.image)
            html_content += f"""
            <div class="page-card">
                <img src="data:image/jpeg;base64,{img_b64}" class="page-img">
                <div class="narration">{page.story_narration}</div>
                <div class="dialogue">"{page.dialogue}"</div>
            </div>
            """
            
        html_content += """
            <div class="footer">- The End -<br>Created by PHODONG</div>
        </body></html>
        """
        return html_content

# ==============================================================================
# 4. 🖥️ UI / VIEW LAYER
# ==============================================================================

def init_session_state():
    if "book_pages" not in st.session_state:
        st.session_state.book_pages = []
    if "book_title" not in st.session_state:
        st.session_state.book_title = "나만의 동화책"
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "single" # single(한장씩) or all(전체보기)

def render_all_pages_view(config: StoryConfig):
    """[추가된 기능] 전체 페이지 이어보기 및 저장"""
    st.markdown(f"<h2 class='font-heading' style='text-align:center; color:#FF9EAA;'>📘 {st.session_state.book_title}</h2>", unsafe_allow_html=True)
    st.caption("아래로 스크롤하여 전체 이야기를 읽어보세요!")

    pages = st.session_state.book_pages
    service = PhodongService() # for download generation

    # 전체 페이지 렌더링
    for page in pages:
        with st.container():
            st.markdown(f"""
            <div class='content-box' style='margin-bottom: 30px;'>
                <div style='text-align:center; margin-bottom:10px; font-family:Jua; color:#A0C4FF;'>
                    {'🧸 표지' if page.is_cover else f'Page {page.page_number}'}
                </div>
            """, unsafe_allow_html=True)
            
            st.image(page.image, use_container_width=True)
            
            st.markdown(f"""
                <div style='margin-top:20px; font-size:1.1rem; line-height:1.6;'>
                    {page.story_narration}
                </div>
                <div class='dialogue-box' style='margin-top:15px; margin-bottom:0;'>
                    <div class='dialogue-text'>"{page.dialogue}"</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # 다운로드 버튼 영역
    st.divider()
    st.markdown("<h3 class='font-heading'>💾 동화책 소장하기</h3>", unsafe_allow_html=True)
    
    html_data = service.create_download_html(pages, config, st.session_state.book_title)
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button(
            label="📘 동화책 다운로드 (HTML)",
            data=html_data,
            file_name=f"{config.child_name}_story.html",
            mime="text/html",
            use_container_width=True,
            type="primary"
        )
    with col_d2:
        if st.button("🔄 처음으로 돌아가기", use_container_width=True):
            st.session_state.book_pages = []
            st.rerun()

def main():
    styles.DesignSystem.inject_css()
    init_session_state()
    service = PhodongService()

    # --- 헤더 ---
    st.markdown("""
        <div class="landing-hero" style="text-align:center; padding-bottom: 20px;">
            <h1 class="landing-title">나만의 동화책 만들기</h1>
            <p class="landing-subtitle">사진을 올리면 <b>포동이</b>가 이야기를 만들어줘요!</p>
        </div>
    """, unsafe_allow_html=True)

    # --- 메인 로직 ---
    # Case 1: 책이 아직 없음 -> 입력 폼 표시
    if not st.session_state.book_pages:
        left_col, right_col = st.columns([1, 1], gap="large")

        with left_col:
            with st.expander("🧸 어떻게 만드나요? (사용법 보기)", expanded=True):
                folder = styles.ArtWork.get_folder(40)
                bear_icon = styles.ArtWork.get_bear(40)
                book = styles.ArtWork.get_book_cover(40)
                st.markdown(styles.Utils.clean_html(f"""
                    <div class="step-container">
                        <div class="step-item step-1">
                            <div>{folder}</div>
                            <div class="step-title" style="color:#A0C4FF;">1. 사진 선택</div>
                            <div class="step-desc">3~5장의 사진을 골라주세요.</div>
                        </div>
                        <div class="step-item step-2">
                            <div>{bear_icon}</div>
                            <div class="step-title" style="color:#FFD580;">2. AI 창작</div>
                            <div class="step-desc">표지 그림과 이야기를 지어줘요.</div>
                        </div>
                        <div class="step-item step-3">
                            <div>{book}</div>
                            <div class="step-title" style="color:#FF9EAA;">3. 책 완성</div>
                            <div class="step-desc">전체 내용을 저장할 수 있어요.</div>
                        </div>
                    </div>
                """), unsafe_allow_html=True)

        with right_col:
            st.markdown(styles.Utils.clean_html("""<div class="landing-action"><div class="action-header">👇 이야기 설정 & 사진 업로드</div>"""), unsafe_allow_html=True)
            
            c_in1, c_in2 = st.columns(2)
            with c_in1: child_name = st.text_input("아이 이름", value="포동이")
            with c_in2: age = st.slider("아이 연령", 3, 9, 5)
            partner_name = st.text_input("함께하는 어른", value="엄마")
            
            c_sel1, c_sel2 = st.columns(2)
            with c_sel1: genre = st.selectbox("장르", GENRE_OPTIONS)
            with c_sel2: purpose = st.selectbox("교육 목표", PURPOSE_OPTIONS)
            
            st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
            
            uploaded_files = st.file_uploader(
                "사진을 순서대로 여러 장 올려주세요! (최대 5장)", 
                type=["jpg", "png", "jpeg"], 
                accept_multiple_files=True,
                label_visibility="collapsed"
            )
            
            process_btn = st.button("✨ 동화책 만들기 시작!", type="primary", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if process_btn:
                if uploaded_files:
                    config = StoryConfig(child_name, partner_name, age, genre, purpose)
                    total_files = len(uploaded_files)
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    temp_book = []
                    context_so_far = "" 
                    character_info = {}
                    
                    try:
                        # 1. 전체 사진 분석 (표지 생성을 위해)
                        status_text.markdown("🎨 **동화책 표지를 그리고 있어요...** (잠시만 기다려주세요!)")
                        all_images = [Image.open(f) for f in uploaded_files]
                        
                        # [표지 생성]
                        # 1-1. 각 사진의 핵심 사물 파악
                        obj_list = []
                        for img in all_images[:3]: # 너무 많으면 오래 걸리니 앞 3장만
                            obj_list.append(service.analyze_image(img))
                        
                        # 1-2. 제목 및 표지 프롬프트 생성
                        cover_info = service.generate_cover_info(obj_list, config)
                        st.session_state.book_title = cover_info.get("title", "나만의 동화책")
                        
                        # 1-3. 표지 이미지 생성 (AI Image Gen)
                        cover_img = service.generate_cover_image(cover_info.get("cover_prompt", ""))
                        
                        # 표지 카드 저장
                        if cover_img:
                            cover_card = StoryCard(
                                page_number=0,
                                character_name="표지",
                                story_narration=f"제목: {st.session_state.book_title}",
                                dialogue=f"지은이: 포동이와 {child_name}",
                                image=cover_img,
                                is_cover=True
                            )
                            temp_book.append(cover_card)

                        # [본문 생성]
                        for i, image in enumerate(all_images):
                            current_page = i + 1
                            status_text.markdown(f"**📖 {current_page}번째 페이지 만드는 중...** ({current_page}/{total_files})")
                            
                            # 사물 인식 (이미 위에서 했지만 정확도를 위해 개별 재호출 or 리스트 활용)
                            obj_desc = obj_list[i] if i < len(obj_list) else service.analyze_image(image)
                            
                            if i == 0:
                                character_info = service.create_character(obj_desc, config)
                            
                            page_data = service.generate_page(
                                page_num=current_page,
                                total_pages=total_files,
                                current_img_desc=obj_desc,
                                character_info=character_info,
                                context_so_far=context_so_far,
                                config=config
                            )
                            
                            audio = service.text_to_speech(page_data['dialogue'])
                            
                            card = StoryCard(
                                page_number=current_page,
                                character_name=character_info.get('name', child_name),
                                current_object=obj_desc,
                                story_narration=page_data['story_narration'],
                                dialogue=page_data['dialogue'],
                                image=image,
                                audio_data=audio
                            )
                            temp_book.append(card)
                            context_so_far += f"\n[Page {current_page}] {page_data['story_narration']}"
                            progress_bar.progress((i + 1) / total_files)
                        
                        st.session_state.book_pages = temp_book
                        st.session_state.config = config
                        st.rerun()

                    except Exception as e:
                        st.error(f"에러 발생: {e}")
                else:
                    st.warning("사진을 최소 1장 이상 올려주세요!")

    # Case 2: 책 완성 -> 전체 보기 모드
    else:
        if "config" in st.session_state:
            render_all_pages_view(st.session_state.config)

if __name__ == "__main__":
    main()