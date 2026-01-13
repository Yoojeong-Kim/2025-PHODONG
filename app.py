import streamlit as st
import os
import json
import io
import logging
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

# [모델 설정] 최신 모델 사용 (사용자 환경 맞춤)
DEFAULT_MODEL = "gemini-2.5-flash" 

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
    page_number: int = 1
    character_name: str = ""   # 주인공 이름 (1페이지에서 결정됨)
    current_object: str = ""   # 현재 페이지 사진에 나온 사물
    story_narration: str = ""
    dialogue: str = ""
    image: Optional[Image.Image] = None # 이미지 객체 직접 저장
    audio_data: Optional[bytes] = None  # 오디오 데이터

# ==============================================================================
# 3. 🧠 AI 서비스 (연속 스토리 생성 로직)
# ==============================================================================
class Utils:
    @staticmethod
    def clean_json_text(text):
        text = text.strip()
        if text.startswith("```json"): text = text[7:]
        elif text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        return text.strip()

class PhodongService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            st.error("🚨 API Key가 없습니다. .env 파일을 확인해주세요.")
            st.stop()
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(DEFAULT_MODEL)

    def analyze_image(self, image: Image.Image) -> str:
        """이미지에 무엇이 있는지 간단히 분석 (주인공/사물 파악용)"""
        prompt = "이 사진에 있는 주요 사물이나 캐릭터가 무엇인지 단답형으로 한글로 알려줘. (예: 빨간 자동차, 곰인형, 칫솔)"
        try:
            res = self.model.generate_content([prompt, image])
            return res.text.strip()
        except:
            return "알 수 없는 물건"

    def create_character(self, object_desc: str, config: StoryConfig) -> dict:
        """[1페이지용] 주인공 캐릭터 설정"""
        prompt = f"""
        당신은 동화 작가입니다. '{object_desc}' 사진을 보고 주인공을 만들어주세요.
        - 독자: {config.age}세, 장르: {config.genre}, 목표: {config.purpose}
        
        [출력 JSON]
        {{
            "name": "캐릭터 이름",
            "personality": "성격 (한 문장)",
            "power": "마법 능력"
        }}
        """
        try:
            res = self.model.generate_content(prompt)
            return json.loads(Utils.clean_json_text(res.text))
        except:
            return {"name": "포동이", "personality": "호기심 많음", "power": "상상하기"}

    def generate_page(self, page_num: int, total_pages: int, current_img_desc: str, 
                      character_info: dict, context_so_far: str, config: StoryConfig) -> dict:
        """[페이지 생성] 이전 줄거리를 바탕으로 현재 페이지 작성"""
        
        # 프롬프트 분기: 첫 페이지 vs 이어지는 페이지
        if page_num == 1:
            context_prompt = "이야기의 시작입니다. 주인공을 소개하고 모험을 시작하세요."
        else:
            context_prompt = f"""
            [지금까지의 줄거리]: {context_so_far}
            
            [현재 상황]: 주인공이 모험 중에 '{current_img_desc}'(을)를 만났습니다.
            이전 내용과 자연스럽게 이어지도록 이야기를 전개하세요.
            """

        final_prompt = f"""
        당신은 아이들을 위한 동화 작가입니다. 총 {total_pages}페이지 중 {page_num}페이지를 작성 중입니다.
        
        [설정]
        - 주인공: {character_info['name']} ({character_info['personality']}, 능력: {character_info['power']})
        - 독자: {config.child_name} ({config.age}세)
        - 장르: {config.genre}
        - 교육 목표: {config.purpose}
        
        {context_prompt}

        [작성 조건]
        1. 말투: {config.age}세 아이에게 읽어주는 다정하고 생동감 넘치는 '해요체'.
        2. 내용: 지문(Narration)은 3~4문장, 대사(Dialogue)는 1~2문장.
        3. {total_pages}페이지가 되면 이야기가 교훈적으로 마무리되어야 합니다.

        [출력 포맷 JSON]
        {{
            "story_narration": "지문 내용...",
            "dialogue": "캐릭터 대사..."
        }}
        """
        
        try:
            res = self.model.generate_content(final_prompt)
            return json.loads(Utils.clean_json_text(res.text))
        except Exception as e:
            logger.error(f"Page Gen Error: {e}")
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

# ==============================================================================
# 4. 🖥️ UI / VIEW LAYER
# ==============================================================================

def init_session_state():
    if "book_pages" not in st.session_state:
        st.session_state.book_pages = [] # 완성된 동화책 페이지들
    if "current_page_idx" not in st.session_state:
        st.session_state.current_page_idx = 0
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False

def render_book_viewer(config: StoryConfig):
    """완성된 동화책을 한 장씩 보여주는 뷰어"""
    pages = st.session_state.book_pages
    idx = st.session_state.current_page_idx
    total = len(pages)
    current_card = pages[idx]

    # [네비게이션 바]
    st.divider()
    col_nav1, col_nav2, col_nav3 = st.columns([1, 6, 1])
    
    with col_nav1:
        if idx > 0:
            if st.button("⬅️ 이전", use_container_width=True):
                st.session_state.current_page_idx -= 1
                st.rerun()
                
    with col_nav2:
        st.markdown(f"<div style='text-align:center; font-family:Jua; font-size:1.2rem; color:#A0C4FF;'>📖 {config.child_name}의 이야기 ( {idx + 1} / {total} )</div>", unsafe_allow_html=True)
        
    with col_nav3:
        if idx < total - 1:
            if st.button("다음 ➡️", use_container_width=True):
                st.session_state.current_page_idx += 1
                st.rerun()

    # [책 내용 표시] - 기존 레퍼런스 스타일 활용
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.2], gap="large")

    with c1:
        # 왼쪽: 이미지 (폴라로이드 스타일)
        st.markdown(f"""
        <div class='polaroid-frame'>
            <div style='text-align:center; margin-bottom:10px; font-family:Jua; color:#FF9EAA;'>
                Scene {idx + 1} : {current_card.current_object}
            </div>
        """, unsafe_allow_html=True)
        st.image(current_card.image, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        # 오른쪽: 이야기 및 대사
        st.markdown(f"""
        <div class='profile-group'>
            <span class='badge-pill badge-pink'>✨ 주인공: {current_card.character_name}</span>
        </div>
        
        <div class='dialogue-box' style='margin-top:20px;'>
            <div class='dialogue-text'>"{current_card.dialogue}"</div>
        </div>
        
        <div class='context-box'>
            {current_card.story_narration}
        </div>
        """, unsafe_allow_html=True)
        
        if current_card.audio_data:
            st.audio(current_card.audio_data, format='audio/mp3')

def main():
    styles.DesignSystem.inject_css()
    init_session_state()
    service = PhodongService()

    # --- 헤더 ---
    bear = styles.ArtWork.get_bear(45)
    c1, c2 = st.columns([0.8, 11.2])
    with c1: st.markdown(f"<div>{bear}</div>", unsafe_allow_html=True)
    with c2: st.markdown(styles.Utils.clean_html("<h3 class='font-heading' style='color:#FF9EAA; margin:0; font-size:1.8rem; line-height:1.5;'>포동 PHODONG</h3>"), unsafe_allow_html=True)
    st.markdown("<hr style='margin: 15px 0 40px 0; border:0; border-top:2px solid #F0F0F0;'>", unsafe_allow_html=True)

    # --- 메인 레이아웃 ---
    # 책이 완성되지 않았을 때만 입력 폼을 보여줌
    if not st.session_state.book_pages:
        left_col, right_col = st.columns([1.3, 1], gap="large")

        with left_col:
            st.markdown("""
                <div class="landing-hero">
                    <h1 class="landing-title">나만의 동화책 만들기</h1>
                    <p class="landing-subtitle">
                        여러 장의 사진을 순서대로 올려주세요.<br>
                        사진들이 모여 <b>하나의 멋진 이야기</b>가 됩니다.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # 가이드 아이콘
            folder = styles.ArtWork.get_folder(40)
            bear_icon = styles.ArtWork.get_bear(40)
            book = styles.ArtWork.get_book_cover(40)
            
            st.markdown(styles.Utils.clean_html(f"""
                <div class="step-container">
                    <div class="step-item step-1">
                        <div>{folder}</div>
                        <div class="step-title" style="color:#A0C4FF;">1. 여러 장 선택</div>
                        <div class="step-desc">이야기에 넣고 싶은 사진을 3~5장 골라주세요.</div>
                    </div>
                    <div class="step-item step-2">
                        <div>{bear_icon}</div>
                        <div class="step-title" style="color:#FFD580;">2. 이야기 연결</div>
                        <div class="step-desc">포동이가 사진 순서대로 이야기를 이어줘요.</div>
                    </div>
                    <div class="step-item step-3">
                        <div>{book}</div>
                        <div class="step-title" style="color:#FF9EAA;">3. 책 완성</div>
                        <div class="step-desc">한 장씩 넘겨보며 동화를 읽어보세요.</div>
                    </div>
                </div>
            """), unsafe_allow_html=True)

        with right_col:
            st.markdown(styles.Utils.clean_html("""<div class="landing-action"><div class="action-header">👇 이야기 설정 & 사진 업로드</div>"""), unsafe_allow_html=True)
            
            # 입력 폼
            c_in1, c_in2 = st.columns(2)
            with c_in1: child_name = st.text_input("아이 이름", value="포동이")
            with c_in2: age = st.slider("아이 연령", 3, 9, 5)
            partner_name = st.text_input("함께하는 어른", value="엄마")
            
            c_sel1, c_sel2 = st.columns(2)
            with c_sel1: genre = st.selectbox("장르", GENRE_OPTIONS)
            with c_sel2: purpose = st.selectbox("교육 목표", PURPOSE_OPTIONS)
            
            st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
            
            # [수정] accept_multiple_files=True 로 변경
            uploaded_files = st.file_uploader(
                "사진을 순서대로 여러 장 올려주세요! (최대 5장 권장)", 
                type=["jpg", "png", "jpeg"], 
                accept_multiple_files=True,
                label_visibility="collapsed"
            )
            
            process_btn = st.button("✨ 동화책 만들기 시작!", type="primary", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # --- 로직 실행 ---
            if process_btn:
                if uploaded_files:
                    config = StoryConfig(child_name, partner_name, age, genre, purpose)
                    total_files = len(uploaded_files)
                    
                    # 진행 상태바
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 임시 저장소
                    temp_book = []
                    context_so_far = "" # 이야기가 이어지도록 내용을 누적
                    character_info = {} # 1페이지에서 만든 캐릭터 정보 저장

                    try:
                        for i, file in enumerate(uploaded_files):
                            current_page = i + 1
                            image = Image.open(file)
                            
                            # 1. 상태 업데이트
                            status_text.markdown(f"**📖 {current_page}번째 페이지 만드는 중...** ({current_page}/{total_files})")
                            
                            # 2. 이미지 분석 (사물 인식)
                            obj_desc = service.analyze_image(image)
                            
                            # 3. 캐릭터 생성 (첫 페이지일 때만)
                            if i == 0:
                                character_info = service.create_character(obj_desc, config)
                            
                            # 4. 스토리 생성 (이전 context 반영)
                            page_data = service.generate_page(
                                page_num=current_page,
                                total_pages=total_files,
                                current_img_desc=obj_desc,
                                character_info=character_info,
                                context_so_far=context_so_far,
                                config=config
                            )
                            
                            # 5. 오디오 생성
                            audio = service.text_to_speech(page_data['dialogue'])
                            
                            # 6. 결과 저장 및 Context 업데이트
                            card = StoryCard(
                                page_number=current_page,
                                character_name=character_info['name'],
                                current_object=obj_desc,
                                story_narration=page_data['story_narration'],
                                dialogue=page_data['dialogue'],
                                image=image,
                                audio_data=audio
                            )
                            temp_book.append(card)
                            
                            # 다음 페이지를 위해 줄거리 누적
                            context_so_far += f"\n[Page {current_page}] {page_data['story_narration']}"
                            
                            # 프로그레스 바 업데이트
                            progress_bar.progress((i + 1) / total_files)
                        
                        # 완료 후 세션 저장
                        st.session_state.book_pages = temp_book
                        st.session_state.config = config # 설정도 저장
                        st.rerun()

                    except Exception as e:
                        st.error(f"에러 발생: {e}")
                else:
                    st.warning("사진을 최소 1장 이상 올려주세요!")

    # --- 책 뷰어 (책이 완성되었을 때만 보임) ---
    else:
        # 상단에 '다시 만들기' 버튼 배치
        c_back, _ = st.columns([1, 5])
        with c_back:
            if st.button("🔄 새로운 책 만들기"):
                st.session_state.book_pages = []
                st.session_state.current_page_idx = 0
                st.rerun()
                
        # 뷰어 렌더링
        if "config" in st.session_state:
            render_book_viewer(st.session_state.config)

if __name__ == "__main__":
    main()