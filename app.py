import streamlit as st
import os
import json
import io
import logging
import base64
from dataclasses import dataclass
from typing import Optional, List
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS

# styles.py 임포트 (CSS 및 아이콘)
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

# [핵심] CSS 강제 주입
if hasattr(styles, 'CSS'):
    st.markdown(styles.CSS, unsafe_allow_html=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("PhodongApp")

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
    character_name: str = ""
    character_type: str = ""   
    personality: str = ""      
    magic_power: str = ""      
    current_object: str = ""
    story_narration: str = ""
    dialogue: str = ""
    image: Optional[Image.Image] = None 
    audio_data: Optional[bytes] = None

# ==============================================================================
# 3. 🧠 AI 서비스
# ==============================================================================
# Utils 클래스 중복 제거 -> styles.Utils 사용

class PhodongService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            st.error("🚨 API Key가 없습니다. .env 파일을 확인해주세요.")
            st.stop()
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(DEFAULT_MODEL)

    def analyze_image(self, image: Image.Image) -> str:
        prompt = "이 사진에 있는 주요 사물이나 캐릭터가 무엇인지 단답형으로 한글로 알려줘."
        try:
            res = self.model.generate_content([prompt, image])
            return res.text.strip()
        except:
            return "알 수 없는 물건"

    def create_character(self, object_desc: str, config: StoryConfig) -> dict:
        prompt = f"""
        당신은 동화 작가입니다. '{object_desc}' 사진을 보고 주인공을 만들어주세요.
        - 독자: {config.age}세, 장르: {config.genre}, 목표: {config.purpose}
        [출력 JSON] {{
            "name": "이름",
            "type": "종류",
            "personality": "성격 (한 문장)",
            "power": "마법 능력 (한 문장)"
        }}
        """
        try:
            res = self.model.generate_content(prompt)
            return json.loads(styles.Utils.clean_html(res.text).replace('```json', '').replace('```', ''))
        except:
            return {"name": "포동이", "type": object_desc, "personality": "호기심 많음", "power": "상상하기"}

    def generate_page(self, page_num: int, total_pages: int, current_img_desc: str, 
                      character_info: dict, context_so_far: str, config: StoryConfig) -> dict:
        if page_num == 1:
            context_prompt = "이야기의 시작입니다. 주인공을 소개하고 모험을 시작하세요."
        else:
            context_prompt = f"""
            [이전 줄거리]: {context_so_far}
            [현재 상황]: 주인공이 '{current_img_desc}'(을)를 만났습니다. 자연스럽게 이어주세요.
            """

        final_prompt = f"""
        동화 작가로서 총 {total_pages}페이지 중 {page_num}페이지를 작성하세요.
        - 주인공: {character_info.get('name')} ({character_info.get('personality')})
        - 독자: {config.child_name} ({config.age}세), 장르: {config.genre}, 목표: {config.purpose}
        {context_prompt}
        [작성 조건] 말투: {config.age}세 아이를 위한 해요체. 지문 3~4문장, 대사 1~2문장.
        [출력 포맷 JSON] {{ "story_narration": "...", "dialogue": "..." }}
        """
        try:
            res = self.model.generate_content(final_prompt)
            return json.loads(styles.Utils.clean_html(res.text).replace('```json', '').replace('```', ''))
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
    if "book_pages" not in st.session_state: st.session_state.book_pages = []
    if "current_page_idx" not in st.session_state: st.session_state.current_page_idx = 0

def render_book_viewer(config: StoryConfig):
    pages = st.session_state.book_pages
    idx = st.session_state.current_page_idx
    total = len(pages)
    card = pages[idx]

    # 네비게이션
    st.markdown(styles.Utils.clean_html(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; color:#888; margin-bottom:20px; padding:0 5px; border-bottom: 2px solid #F0F0F0; padding-bottom:15px;">
            <span class='font-heading' style='font-size:1.3rem; color:#FF9EAA;'>📖 {config.child_name}의 모험</span>
            <span class='font-heading' style='font-size:1.1rem; background:#FFF; padding:6px 15px; border:2px solid #F0F0F0; border-radius:15px; color:#A0C4FF;'>
                Page {idx + 1} / {total}
            </span>
        </div>
    """), unsafe_allow_html=True)

    col_img, col_txt = st.columns([1, 1], gap="large")

    with col_img:
        img_b64 = styles.Utils.image_to_base64(card.image) if hasattr(styles.Utils, 'image_to_base64') else ""
        # 임시 base64 변환 로직 (styles에 없을 경우 대비)
        if not img_b64 and card.image:
            buffered = io.BytesIO()
            card.image.save(buffered, format="JPEG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()
        
        img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else ""
        
        st.markdown(styles.Utils.clean_html(f"""
            <div class='polaroid-frame'>
                <img src='{img_src}' class='polaroid-img'>
                <div class='polaroid-label'>Scene {card.page_number} : {card.current_object}</div>
            </div>
            <div class='profile-group'>
                <span class='badge-pill badge-pink'>✨ {styles.Utils.escape(card.character_name)} ({styles.Utils.escape(card.character_type)})</span>
                <div style="margin-top:12px;">
                    <span class='badge-pill badge-yellow'>💖 {styles.Utils.escape(card.personality)}</span>
                </div>
                <div style="margin-top:10px; font-size: 0.95rem; color: #555; background: #E0F2F1; padding: 10px; border-radius: 8px;">
                    ⚡ <b>능력:</b> {styles.Utils.escape(card.magic_power)}
                </div>
            </div>
        """), unsafe_allow_html=True)

    with col_txt:
        st.markdown(styles.Utils.clean_html(f"""
            <div style="padding-top:10px;">
                <div class='dialogue-box'>
                    <div class='dialogue-text'>"{styles.Utils.escape(card.dialogue)}"</div>
                </div>
                <div class='context-box'>
                    <strong style='color:#A0C4FF; font-family:"Jua"; display:block; margin-bottom:10px; font-size:1.15rem;'>상황 설명</strong>
                    {styles.Utils.escape(card.story_narration)}
                </div>
            </div>
        """), unsafe_allow_html=True)
        
        if card.audio_data:
            st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
            st.audio(card.audio_data, format='audio/mp3')

    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1, 2, 1])
    with b1:
        if idx > 0 and st.button("⬅️ 이전", use_container_width=True):
            st.session_state.current_page_idx -= 1
            st.rerun()
    with b3:
        if idx < total - 1 and st.button("다음 ➡️", use_container_width=True):
            st.session_state.current_page_idx += 1
            st.rerun()
        elif idx == total - 1:
            if st.button("🔄 처음으로", type="primary", use_container_width=True):
                st.session_state.book_pages = []
                st.session_state.current_page_idx = 0
                st.rerun()

def main():
    init_session_state()
    service = PhodongService()

    bear = styles.ArtWork.get_bear(45)
    c1, c2 = st.columns([0.8, 11.2])
    with c1: st.markdown(f"<div>{bear}</div>", unsafe_allow_html=True)
    with c2: st.markdown(styles.Utils.clean_html("<h3 class='font-heading' style='color:#FF9EAA; margin:0; font-size:1rem; line-height:1;'>체험용 모바일 프로토타입</h3>"), unsafe_allow_html=True)
    st.markdown("<hr style='margin: 15px 0 40px 0; border:0; border-top:2px solid #F0F0F0;'>", unsafe_allow_html=True)

    # [수정] 타이틀 태그를 div.landing-title 로 변경하여 CSS 적용 확실하게 함
    st.markdown("""
        <div class="landing-hero" style="text-align:center; padding-bottom: 20px;">
            <div class="landing-title">포동 PHODONG</div>
            <p class="landing-subtitle">아이의 소중한 순간들이<br>세상에 하나뿐인 동화책이 됩니다!</p>
        </div>
    """, unsafe_allow_html=True)

    if not st.session_state.book_pages:
        left_col, right_col = st.columns([1, 1], gap="large")
        with left_col:
            with st.expander("🧸 사용법 보기", expanded=True):
                folder = styles.ArtWork.get_folder(40)
                bear = styles.ArtWork.get_bear(40)
                book = styles.ArtWork.get_book_cover(40)
                st.markdown(styles.Utils.clean_html(f"""
                    <div class="step-container">
                        <div class="step-item step-1"><div>{folder}</div><div class="step-title" style="color:#A0C4FF;">1. 사진 선택</div><div class="step-desc">여러 장의 사진을 골라주세요.</div></div>
                        <div class="step-item step-2"><div>{bear}</div><div class="step-title" style="color:#FFD580;">2. AI 창작</div><div class="step-desc">사진 순서대로 이야기를 지어요.</div></div>
                        <div class="step-item step-3"><div>{book}</div><div class="step-title" style="color:#FF9EAA;">3. 책 완성</div><div class="step-desc">나만의 동화책을 읽어보세요.</div></div>
                    </div>
                """), unsafe_allow_html=True)

        with right_col:
            with st.expander("📝 이야기 설정 & 사진 업로드", expanded=True):
                st.markdown("<div style='padding: 10px 5px;'>", unsafe_allow_html=True)
                c_in1, c_in2 = st.columns(2)

                with c_in1: 
                    child_name = st.text_input("아이 이름", value="", placeholder="예) 민준")
                with c_in2: 
                    age = st.number_input("아이 연령", min_value=1, max_value=13, value=5, step=1)

                partner_name = st.text_input("단짝 이름", value="", placeholder="예) 포동이")

                c_sel1, c_sel2 = st.columns(2)
                with c_sel1: genre = st.selectbox("장르", GENRE_OPTIONS)
                with c_sel2: purpose = st.selectbox("교육 목표", PURPOSE_OPTIONS)
                st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
                
                uploaded_files = st.file_uploader(
                    "사진을 순서대로 여러 장 올려주세요! (최대 3장 체험 가능)", 
                    type=["jpg", "png", "jpeg"], 
                    accept_multiple_files=True,
                    label_visibility="collapsed"
                )
                st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
                process_btn = st.button("✨ 동화책 만들기 시작!", type="primary", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            if process_btn:
                if uploaded_files:
                    # --- [수정된 부분 시작] ---
                    if len(uploaded_files) > 3:
                        st.error("🚫 체험판에서는 사진을 최대 3장까지만 업로드할 수 있어요!")
                    else:
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
                                if i == 0: character_info = service.create_character(obj_desc, config)
                                
                                page_data = service.generate_page(current_page, total_files, obj_desc, character_info, context_so_far, config)
                                audio = service.text_to_speech(page_data['dialogue'])
                                
                                temp_book.append(StoryCard(
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
                                ))
                                context_so_far += f"\n[Page {current_page}] {page_data['story_narration']}"
                                progress_bar.progress((i + 1) / total_files)
                            
                            st.session_state.book_pages = temp_book
                            st.session_state.config = config
                            st.rerun()

                        except Exception as e:
                            st.error(f"에러 발생: {e}")
                else:
                    st.warning("사진을 최소 1장 이상 올려주세요!")

    else:
        if "config" in st.session_state:
            render_book_viewer(st.session_state.config)

if __name__ == "__main__":
    main()