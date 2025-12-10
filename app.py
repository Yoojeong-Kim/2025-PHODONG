import time
import io
import html
import streamlit as st
from PIL import Image

# 분리된 로직 임포트
from phodong_logic import (
    StoryConfig, StoryCard, LLMService, AudioService, Utils,
    GENRE_OPTIONS, PURPOSE_OPTIONS
)

# ==============================================================================
# CONFIG & STATE
# ==============================================================================
st.set_page_config(page_title="포동 PHODONG", page_icon="🧸", layout="wide", initial_sidebar_state="collapsed")

# API 키 처리 (로컬 .env 또는 Streamlit Cloud Secrets)
def get_api_key():
    import os
    # 1. 로컬 환경 변수 확인
    key = os.getenv("GOOGLE_API_KEY")
    # 2. Streamlit Cloud Secrets 확인
    if not key and "GOOGLE_API_KEY" in st.secrets:
        key = st.secrets["GOOGLE_API_KEY"]
    return key

class AppState:
    @staticmethod
    def init():
        if "page_idx" not in st.session_state: st.session_state.page_idx = 0
        if "show_final" not in st.session_state: st.session_state.show_final = False
        if "uploaded_files" not in st.session_state: st.session_state.uploaded_files = None
        if "story_config" not in st.session_state: st.session_state.story_config = StoryConfig()
        if "story_cards" not in st.session_state: st.session_state.story_cards = []
        if "final_story_text" not in st.session_state: st.session_state.final_story_text = None
        if "final_audio_data" not in st.session_state: st.session_state.final_audio_data = None
        if "generation_complete" not in st.session_state: st.session_state.generation_complete = False
        if "image_storage" not in st.session_state: st.session_state.image_storage = {}

# ==============================================================================
# DESIGN SYSTEM (CSS & SVG)
# ==============================================================================
class ArtWork:
    @staticmethod
    def get_bear(size=100):
        return f"""<svg width="{size}" height="{size}" viewBox="0 0 100 100" fill="none" xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)"><circle cx="50" cy="55" r="35" fill="#D6B898"/><circle cx="35" cy="25" r="12" fill="#D6B898"/><circle cx="65" cy="25" r="12" fill="#D6B898"/><circle cx="35" cy="25" r="6" fill="#EAC7A8"/><circle cx="65" cy="25" r="6" fill="#EAC7A8"/><ellipse cx="50" cy="60" rx="14" ry="10" fill="#FFF0F5"/><circle cx="50" cy="56" r="4" fill="#5D4037"/><circle cx="42" cy="48" r="3" fill="#333"/><circle cx="58" cy="48" r="3" fill="#333"/><path d="M50 60V65" stroke="#5D4037" stroke-width="2" stroke-linecap="round"/><path d="M46 65C46 65 48 68 50 68C52 68 54 65 54 65" stroke="#5D4037" stroke-width="2" stroke-linecap="round"/></svg>"""
    
    @staticmethod
    def get_book_cover(size=60):
        return f"""<svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none" xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)"><rect x="10" y="8" width="44" height="48" rx="4" fill="#FF9EAA"/><rect x="14" y="8" width="6" height="48" fill="#FF7B8E"/><rect x="24" y="18" width="26" height="4" rx="2" fill="#FFF5F7"/><rect x="24" y="26" width="18" height="4" rx="2" fill="#FFF5F7"/><circle cx="36" cy="42" r="8" fill="#FFD580"/></svg>"""

    @staticmethod
    def get_camera():
        return f"""<svg width="100%" height="100%" viewBox="0 0 200 200" fill="none" xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)"><rect width="200" height="200" fill="#F8F9FA"/><rect x="50" y="60" width="100" height="80" rx="12" fill="#A0C4FF"/><circle cx="100" cy="100" r="30" fill="#FFFFFF" stroke="#89C4F4" stroke-width="6"/><circle cx="100" cy="100" r="15" fill="#FFD580"/><rect x="120" y="50" width="20" height="10" rx="3" fill="#89C4F4"/><text x="100" y="175" font-family="'Jua', sans-serif" font-size="16" fill="#89C4F4" text-anchor="middle">이미지 준비 중</text></svg>"""

def inject_css():
    st.markdown("""
    <style>
        /* 1. 폰트 및 기본 테마 설정 (기존 유지) */
        @import url('https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&display=swap');
        :root { --bg-base: #FFFBF8; --primary: #FF9EAA; --secondary: #FFD580; --tertiary: #A0C4FF; }
        .stApp { background: linear-gradient(135deg, #FFFBF8 0%, #FFF5F7 50%, #F0F7FF 100%); font-family: 'Gowun Dodum', sans-serif; }
        h1, h2, h3 { font-family: 'Jua', sans-serif; color: #3A3A3A; }
        
        /* 2. UI 컴포넌트 스타일 (기존 유지) */
        .stButton>button { border-radius: 12px; background: linear-gradient(45deg, var(--primary), #FF8495); color: white; font-family: 'Jua'; border: none; height: 50px; font-size: 1.2rem; }
        .polaroid-frame { background: white; padding: 15px 15px 50px 15px; border: 1px solid #EEE; box-shadow: 0 8px 20px rgba(0,0,0,0.05); border-radius: 4px; }
        .polaroid-img { width: 100%; border-radius: 2px; border: 1px solid #F0F0F0; }
        .polaroid-label { text-align: center; margin-top: 15px; font-family: 'Jua'; color: #BBB; }
        .dialogue-box { background: #FFFBE6; border: 2px solid #FFF5C4; border-radius: 20px 20px 20px 0; padding: 25px; margin-bottom: 20px; font-family: 'Jua'; font-size: 1.3rem; color: #5D4037; }
        .loader-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: white; z-index: 9999; display: flex; flex-direction: column; justify-content: center; align-items: center; }

        /* 🔥 3. [가져오신 코드 응용] Streamlit UI 강제 숨기기 🔥 */
        div[data-testid="stToolbar"] {
            visibility: hidden;
            height: 0%;
            position: fixed;
        }
        div[data-testid="stDecoration"] {
            visibility: hidden;
            height: 0%;
            position: fixed;
        }
        div[data-testid="stStatusWidget"] {
            visibility: hidden;
            height: 0%;
            position: fixed;
        }
        #MainMenu {
            visibility: hidden;
            height: 0%;
        }
        header {
            visibility: hidden;
            height: 0%;
        }
        footer {
            visibility: hidden;
            height: 0%;
        }
        
        /* 🔥 4. [추가] 혹시 모를 'Hosted with Streamlit' 뱃지 안전장치 🔥 */
        .viewerBadge_container__1QSob, [class*="viewerBadge"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# UI COMPONENTS
# ==============================================================================
def render_loader():
    st.markdown("""
        <div class="loader-overlay">
            <h2 style='color:#FF9EAA; font-family:"Jua";'>✨ 이야기를 짓고 있어요...</h2>
            <p style='color:#A0C4FF;'>잠시만 기다려주세요!</p>
        </div>
    """, unsafe_allow_html=True)

def process_images(files, config):
    try:
        api_key = get_api_key()
        llm_service = LLMService(api_key)
    except Exception as e:
        st.error(f"API 키 설정 오류: {e}")
        return

    progress_bar = st.progress(0)
    cards = []
    
    for i, file in enumerate(files):
        bytes_data = file.getvalue()
        pil_image = Image.open(io.BytesIO(bytes_data))
        
        # Logic 호출
        card = llm_service.generate_story_card(io.BytesIO(bytes_data), config)
        
        if card:
            card.image_key = f"img_{i}"
            st.session_state.image_storage[card.image_key] = pil_image
            cards.append(card)
        
        progress_bar.progress((i + 1) / len(files))
        time.sleep(0.5)

    st.session_state.story_cards = cards
    st.session_state.generation_complete = True
    st.rerun()

def landing_page():
    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        st.markdown(f"<h1 style='font-size:3.5rem; color:#FF9EAA;'>포동 PHODONG</h1>", unsafe_allow_html=True)
        st.markdown("### 우리 아이를 위한 맞춤형 AI 동화책")
        st.markdown(ArtWork.get_bear(150), unsafe_allow_html=True)
    
    with c2:
        with st.form("config_form"):
            st.session_state.story_config.child_name = st.text_input("아이 이름", st.session_state.story_config.child_name)
            st.session_state.story_config.partner_name = st.text_input("친구 이름", st.session_state.story_config.partner_name)
            st.session_state.story_config.age = st.text_input("나이 (숫자)", st.session_state.story_config.age)
            
            st.markdown("#### 장르 및 목적")
            c_g, c_p = st.columns(2)
            with c_g: 
                genre = st.selectbox("장르", GENRE_OPTIONS)
            with c_p:
                purpose = st.selectbox("목적", PURPOSE_OPTIONS)
            
            uploaded_files = st.file_uploader("사진 업로드 (2장 이상)", type=["png", "jpg"], accept_multiple_files=True)
            submit = st.form_submit_button("동화 만들기 시작!")

            if submit:
                if not uploaded_files:
                    st.error("사진을 올려주세요!")
                else:
                    st.session_state.story_config.genre = genre
                    st.session_state.story_config.purpose = purpose
                    st.session_state.uploaded_files = uploaded_files
                    process_images(uploaded_files, st.session_state.story_config)

def scene_view():
    idx = st.session_state.page_idx
    cards = st.session_state.story_cards
    if not cards: return st.error("생성된 카드가 없습니다.")
    
    card = cards[idx]
    pil_image = st.session_state.image_storage.get(card.image_key)
    b64_img = Utils.get_image_base64(pil_image)
    
    st.markdown(f"<h3 style='text-align:center;'>Scene {idx+1} / {len(cards)}</h3>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        img_src = f"data:image/jpeg;base64,{b64_img}" if b64_img else ""
        st.markdown(f"""
            <div class='polaroid-frame'>
                <img src='{img_src}' class='polaroid-img'>
                <div class='polaroid-label'>{card.character_name}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""
            <div class='dialogue-box'>"{html.escape(card.dialogue)}"</div>
            <div style='background:white; padding:20px; border-left:4px solid #A0C4FF; color:#555;'>
                <strong>상황:</strong> {html.escape(card.story_narration)}<br><br>
                <small>성격: {card.personality} | 마법: {card.magic_power}</small>
            </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if idx > 0 and st.button("⬅️ 이전"):
            st.session_state.page_idx -= 1
            st.rerun()
    with col3:
        if idx < len(cards) - 1:
            if st.button("다음 ➡️"):
                st.session_state.page_idx += 1
                st.rerun()
        else:
            if st.button("✨ 완성하기", type="primary"):
                st.session_state.show_final = True
                st.rerun()

def final_view():
    if not st.session_state.final_story_text:
        render_loader()
        llm = LLMService(get_api_key())
        text = llm.generate_final_story(st.session_state.story_cards, st.session_state.story_config)
        audio = AudioService.create(text)
        st.session_state.final_story_text = text
        st.session_state.final_audio_data = audio
        st.rerun()

    st.markdown(ArtWork.get_book_cover(80), unsafe_allow_html=True)
    st.markdown("## 나만의 동화책이 완성되었어요!")
    st.markdown("---")
    
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.markdown(f"<div style='white-space: pre-wrap; line-height:2.2; font-size:1.1rem;'>{st.session_state.final_story_text}</div>", unsafe_allow_html=True)
    with c2:
        if st.session_state.final_audio_data:
            st.audio(st.session_state.final_audio_data, format="audio/mp3")
        
        if st.button("처음으로 돌아가기"):
            st.session_state.clear()
            st.rerun()

# ==============================================================================
# MAIN
# ==============================================================================
def main():
    AppState.init()
    inject_css()
    
    if not st.session_state.generation_complete:
        landing_page()
    elif st.session_state.show_final:
        final_view()
    else:
        scene_view()

if __name__ == "__main__":
    main()