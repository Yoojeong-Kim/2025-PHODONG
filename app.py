import streamlit as st
import os
import json
import io
import logging
import base64
import html
from dataclasses import dataclass
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

# [모델 설정] 최신 모델 사용
DEFAULT_MODEL = "gemini-2.5-flash" 

GENRE_OPTIONS = ["전래동화", "판타지", "히어로", "요정", "일상", "자동차", "공주/왕자", "추리", "우주", "로봇", "동물", "공룡"]
PURPOSE_OPTIONS = ["안전 교육", "예절&규칙", "생활 습관", "어휘력 향상", "세계&다양성", "창의력/사고력", "기초과학", "자존감 높이기"]

# ==============================================================================
# 2. 📦 데이터 구조 (디자인을 위해 필드 추가됨)
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
    character_name: str = ""
    character_type: str = ""   # [추가] 캐릭터 종류 (예: 곰인형)
    personality: str = ""      # [추가] 성격
    magic_power: str = ""      # [추가] 능력
    current_object: str = ""
    story_narration: str = ""
    dialogue: str = ""
    image: Optional[Image.Image] = None 
    audio_data: Optional[bytes] = None

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
        """PIL 이미지를 HTML 표시용 Base64 코드로 변환"""
        if image is None: return ""
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode()

    @staticmethod
    def escape(text: str) -> str:
        """HTML 특수문자 처리"""
        return html.escape(str(text))

class PhodongService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            st.error("🚨 API Key가 없습니다. .env 파일을 확인해주세요.")
            st.stop()
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(DEFAULT_MODEL)

    def analyze_image(self, image: Image.Image) -> str:
        """이미지에 무엇이 있는지 간단히 분석"""
        prompt = "이 사진에 있는 주요 사물이나 캐릭터가 무엇인지 단답형으로 한글로 알려줘."
        try:
            res = self.model.generate_content([prompt, image])
            return res.text.strip()
        except:
            return "알 수 없는 물건"

    def create_character(self, object_desc: str, config: StoryConfig) -> dict:
        """[1페이지용] 주인공 캐릭터 설정 (상세 정보 요청)"""
        prompt = f"""
        당신은 동화 작가입니다. '{object_desc}' 사진을 보고 주인공을 만들어주세요.
        - 독자: {config.age}세, 장르: {config.genre}, 목표: {config.purpose}
        
        [출력 JSON]
        {{
            "name": "이름 (예: 포동이)",
            "type": "종류 (예: 용감한 곰인형)",
            "personality": "성격 (한 문장)",
            "power": "마법 능력 (한 문장)"
        }}
        """
        try:
            res = self.model.generate_content(prompt)
            return json.loads(Utils.clean_json_text(res.text))
        except:
            return {"name": "포동이", "type": object_desc, "personality": "호기심 많음", "power": "상상하기"}

    def generate_page(self, page_num: int, total_pages: int, current_img_desc: str, 
                      character_info: dict, context_so_far: str, config: StoryConfig) -> dict:
        """페이지 내용 생성"""
        
        if page_num == 1:
            context_prompt = "이야기의 시작입니다. 주인공을 소개하고 모험을 시작하세요."
        else:
            context_prompt = f"""
            [이전 줄거리]: {context_so_far}
            [현재 상황]: 주인공이 '{current_img_desc}'(을)를 만났습니다. 자연스럽게 이어주세요.
            """

        final_prompt = f"""
        동화 작가로서 총 {total_pages}페이지 중 {page_num}페이지를 작성하세요.
        
        [설정]
        - 주인공: {character_info.get('name')} ({character_info.get('personality')})
        - 독자: {config.child_name} ({config.age}세), 장르: {config.genre}
        - 교육 목표: {config.purpose}
        
        {context_prompt}

        [작성 조건]
        1. 말투: {config.age}세 아이를 위한 따뜻한 '해요체'.
        2. 분량: 지문(Narration) 3~4문장, 대사(Dialogue) 1~2문장.
        3. {total_pages}페이지에서 이야기가 교훈적으로 끝나야 함.

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
# 4. 🖥️ UI / VIEW LAYER (디자인 적용됨!)
# ==============================================================================

def init_session_state():
    if "book_pages" not in st.session_state:
        st.session_state.book_pages = []
    if "current_page_idx" not in st.session_state:
        st.session_state.current_page_idx = 0

def render_book_viewer(config: StoryConfig):
    """[디자인 적용] 완성된 동화책 뷰어"""
    pages = st.session_state.book_pages
    idx = st.session_state.current_page_idx
    total = len(pages)
    card = pages[idx]

    # 1. 상단 네비게이션
    st.markdown(styles.Utils.clean_html(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; color:#888; margin-bottom:20px; padding:0 5px; border-bottom: 2px solid #F0F0F0; padding-bottom:15px;">
            <span class='font-heading' style='font-size:1.3rem; color:#FF9EAA;'>📖 {config.child_name}의 모험</span>
            <span class='font-heading' style='font-size:1.1rem; background:#FFF; padding:6px 15px; border:2px solid #F0F0F0; border-radius:15px; color:#A0C4FF;'>
                Page {idx + 1} / {total}
            </span>
        </div>
    """), unsafe_allow_html=True)

    # 2. 메인 콘텐츠 (2컬럼 레이아웃)
    col_img, col_txt = st.columns([1, 1], gap="large")

    # [왼쪽] 폴라로이드 사진 + 프로필 박스
    with col_img:
        img_b64 = Utils.image_to_base64(card.image)
        img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else ""
        
        # 폴라로이드 프레임
        st.markdown(styles.Utils.clean_html(f"""
            <div class='polaroid-frame'>
                <img src='{img_src}' class='polaroid-img'>
                <div class='polaroid-label'>Scene {card.page_number} : {card.current_object}</div>
            </div>
        """), unsafe_allow_html=True)

        # 프로필 박스 (민트색)
        st.markdown(styles.Utils.clean_html(f"""
            <div class='profile-group'>
                <span class='badge-pill badge-pink'>✨ {Utils.escape(card.character_name)} ({Utils.escape(card.character_type)})</span>
                <div style="margin-top:12px;">
                    <span class='badge-pill badge-yellow'>💖 {Utils.escape(card.personality)}</span>
                </div>
                <div style="margin-top:10px; font-size: 0.95rem; color: #555; background: #E0F2F1; padding: 10px; border-radius: 8px;">
                    ⚡ <b>능력:</b> {Utils.escape(card.magic_power)}
                </div>
            </div>
        """), unsafe_allow_html=True)

    # [오른쪽] 대사(노랑) + 지문(파랑)
    with col_txt:
        st.markdown(styles.Utils.clean_html(f"""
            <div style="padding-top:10px;">
                <div class='dialogue-box'>
                    <div class='dialogue-text'>
                        "{Utils.escape(card.dialogue)}"
                    </div>
                </div>
                
                <div class='context-box'>
                    <strong style='color:#A0C4FF; font-family:"Jua"; display:block; margin-bottom:10px; font-size:1.15rem;'>
                        상황 설명
                    </strong>
                    {Utils.escape(card.story_narration)}
                </div>
            </div>
        """), unsafe_allow_html=True)
        
        if card.audio_data:
            st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
            st.audio(card.audio_data, format='audio/mp3')

    # 3. 하단 버튼
    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)
    b_col1, b_col2, b_col3 = st.columns([1, 2, 1])

    with b_col1:
        if idx > 0:
            if st.button("⬅️ 이전", use_container_width=True):
                st.session_state.current_page_idx -= 1
                st.rerun()

    with b_col3:
        if idx < total - 1:
            if st.button("다음 ➡️", use_container_width=True):
                st.session_state.current_page_idx += 1
                st.rerun()
        else:
            if st.button("🔄 처음으로", type="primary", use_container_width=True):
                st.session_state.book_pages = []
                st.session_state.current_page_idx = 0
                st.rerun()

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

    # --- 메인 레이아웃 (책 생성 전) ---
    if not st.session_state.book_pages:
        # 모바일 레이아웃 고려: 제목은 밖으로 뺌
        st.markdown("""
            <div class="landing-hero" style="text-align:center; padding-bottom: 20px;">
                <h1 class="landing-title">나만의 동화책 만들기</h1>
                <p class="landing-subtitle">사진을 올리면 <b>포동이</b>가 이야기를 만들어줘요!</p>
            </div>
        """, unsafe_allow_html=True)

        left_col, right_col = st.columns([1, 1], gap="large")

        with left_col:
            # 모바일을 위해 가이드는 확장형으로
            with st.expander("🧸 사용법 보기 (클릭)", expanded=True):
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
            
            c_in1, c_in2 = st.columns(2)
            with c_in1: child_name = st.text_input("아이 이름", value="포동이")
            with c_in2: age = st.slider("아이 연령", 3, 9, 5)
            partner_name = st.text_input("함께하는 어른", value="엄마")
            
            c_sel1, c_sel2 = st.columns(2)
            with c_sel1: genre = st.selectbox("장르", GENRE_OPTIONS)
            with c_sel2: purpose = st.selectbox("교육 목표", PURPOSE_OPTIONS)
            
            st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
            
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
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    temp_book = []
                    context_so_far = ""
                    character_info = {} 

                    try:
                        for i, file in enumerate(uploaded_files):
                            current_page = i + 1
                            image = Image.open(file)
                            
                            status_text.markdown(f"**📖 {current_page}번째 페이지 만드는 중...** ({current_page}/{total_files})")
                            
                            obj_desc = service.analyze_image(image)
                            
                            # 1페이지에서만 캐릭터 생성
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
                            
                            # StoryCard에 상세 정보 저장 (디자인에 필요)
                            card = StoryCard(
                                page_number=current_page,
                                character_name=character_info.get('name', '알 수 없음'),
                                character_type=character_info.get('type', obj_desc),
                                personality=character_info.get('personality', '-'),
                                magic_power=character_info.get('power', '-'),
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

    # --- 책 뷰어 (책 완성 후) ---
    else:
        if "config" in st.session_state:
            render_book_viewer(st.session_state.config)

if __name__ == "__main__":
    main()