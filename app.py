import time
import io
import streamlit as st
from PIL import Image

# 로직 임포트
from phodong_upload import (
    StoryConfig, StoryCard, LLMService, AudioService, Utils,
    GENRE_OPTIONS, PURPOSE_OPTIONS
)
from phodong_live import CameraManager

# ==============================================================================
# CONFIG & CSS
# ==============================================================================
st.set_page_config(page_title="포동 PHODONG", page_icon="🧸", layout="wide")

def get_api_key():
    import os
    key = os.getenv("GOOGLE_API_KEY")
    if not key and "GOOGLE_API_KEY" in st.secrets:
        key = st.secrets["GOOGLE_API_KEY"]
    return key

def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&display=swap');
        
        :root { --bg-base: #FFFBF8; --primary: #FF9EAA; --secondary: #FFD580; --tertiary: #A0C4FF; --primary-soft: #FFF0F5; }
        
        /* 전체 배경 및 폰트 */
        .stApp { background: linear-gradient(135deg, #FFFBF8 0%, #FFF5F7 50%, #F0F7FF 100%); font-family: 'Gowun Dodum', sans-serif; }
        h1, h2, h3, h4 { font-family: 'Jua', sans-serif; color: #3A3A3A; }
        
        /* 상단 여백 제거 */
        .block-container { padding-top: 2rem !important; }

        /* ================= 랜딩 페이지 카드 버튼 스타일 (핵심!) ================= */
        .card-container {
            text-align: center;
            padding: 40px 30px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            border: 3px solid transparent;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            transition: all 0.3s ease;
        }
        
        /* Streamlit 버튼 투명화 및 카드 덮어씌우기 */
        [data-testid="stButton"] > button[key^="btn_landing"] {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
            height: auto !important;
            width: 100% !important;
            box-shadow: none !important;
            color: inherit !important;
            font-family: inherit !important;
            font-size: inherit !important;
        }

        /* 호버 효과 */
        [data-testid="stButton"]:hover > button[key^="btn_landing"] .card-container {
            transform: translateY(-7px);
            box-shadow: 0 15px 35px rgba(255, 158, 170, 0.2);
            border-color: var(--primary);
            background-color: var(--primary-soft);
        }
        /* ===================================================================== */

        /* 기본 버튼 스타일 */
        .stButton>button:not([key^="btn_landing"]) { 
            border-radius: 12px !important; 
            background: linear-gradient(45deg, var(--primary), #FF8495) !important; 
            color: white !important; 
            font-family: 'Jua' !important; 
            border: none !important; 
            height: 54px !important; 
            font-size: 1.2rem !important; 
            width: 100% !important; 
            box-shadow: 0 4px 15px rgba(255, 158, 170, 0.3) !important;
            transition: all 0.2s ease-in-out !important;
        }
        .stButton>button:not([key^="btn_landing"]):hover { 
            transform: translateY(-3px); 
            box-shadow: 0 8px 20px rgba(255, 158, 170, 0.5) !important; 
        }

        /* 2차 버튼 */
        button[kind="secondary"] {
            background: white !important;
            color: #555 !important;
            border: 2px solid #EEE !important;
        }

        /* 폴라로이드 & 대사창 */
        .polaroid-frame { 
            background: white; padding: 15px 15px 50px 15px; 
            border: 1px solid #EEE; box-shadow: 0 8px 20px rgba(0,0,0,0.05); 
            border-radius: 8px; transform: rotate(-1deg);
        }
        .polaroid-img { width: 100%; border-radius: 2px; border: 1px solid #F0F0F0; }
        .polaroid-label { text-align: center; margin-top: 15px; font-family: 'Jua'; color: #BBB; font-size: 1.1rem; }

        .dialogue-box { 
            background: #FFFBE6; border: 2px solid #FFF5C4; 
            border-radius: 20px 20px 20px 0; padding: 30px; 
            margin-bottom: 20px; font-family: 'Jua'; font-size: 1.4rem; color: #5D4037; 
            line-height: 1.6; box-shadow: 0 4px 10px rgba(255, 235, 59, 0.1);
        }
        
        .loader-overlay { 
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
            background: rgba(255, 255, 255, 0.95); z-index: 9999; 
            display: flex; flex-direction: column; justify-content: center; align-items: center; 
        }

        /* UI 숨기기 */
        div[data-testid="stToolbar"], div[data-testid="stDecoration"], div[data-testid="stStatusWidget"], #MainMenu, header, footer {
            visibility: hidden; height: 0%; position: fixed;
        }
        .viewerBadge_container__1QSob, [class*="viewerBadge"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

class AppState:
    @staticmethod
    def init():
        keys = {
            "mode": None, "page_idx": 0, "show_final": False, 
            "story_cards": [], "final_story_text": None, "final_audio_data": None,
            "generation_complete": False, "image_storage": {}
        }
        for k, v in keys.items():
            if k not in st.session_state: st.session_state[k] = v
        if "story_config" not in st.session_state: st.session_state.story_config = StoryConfig()

# ==============================================================================
# UI PAGES
# ==============================================================================
def landing_page():
    st.markdown("<div style='height: 8vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center; font-size:4.5rem; color:#FF9EAA; text-shadow: 3px 3px 0 #FFF; margin-bottom: 10px;'>🧸 포동 PHODONG</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888; font-size:1.3rem; margin-bottom:70px; font-weight: 500;'>우리 아이를 위한 세상에 하나뿐인 AI 동화책</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2.2, 1])
    with c2:
        col_up, col_cam = st.columns(2, gap="large")
        
        with col_up:
            btn_html_up = """
            <div class="card-container">
                <div style="font-size:5rem; margin-bottom:20px;">📂</div>
                <h3 style="margin:0; color:#4A4A4A; font-size: 1.8rem;">앨범 업로드</h3>
                <p style="color:#AAA; font-size:1rem; margin-top: 10px;">찍어둔 사진으로 만들어요</p>
            </div>
            """
            if st.button(btn_html_up, key="btn_landing_up"):
                st.session_state.mode = "upload"; st.rerun()

        with col_cam:
            btn_html_cam = """
            <div class="card-container">
                <div style="font-size:5rem; margin-bottom:20px;">📸</div>
                <h3 style="margin:0; color:#4A4A4A; font-size: 1.8rem;">카메라 촬영</h3>
                <p style="color:#AAA; font-size:1rem; margin-top: 10px;">지금 바로 찍어서 만들어요</p>
            </div>
            """
            if st.button(btn_html_cam, key="btn_landing_cam"):
                st.session_state.mode = "camera"; st.rerun()

def render_config():
    col_nav1, col_nav2 = st.columns([1, 5])
    with col_nav1:
        if st.button("🏠 처음으로"):
            st.session_state.mode = None
            st.session_state.camera_captures = []
            st.rerun()
            
    # 👇 [수정됨] 문구 변경: "아이의 이야기 설정" -> "어떤 이야기를 만들어볼까요?"
    st.markdown(f"### ⚙️ 어떤 이야기를 만들어볼까요?")
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        st.session_state.story_config.child_name = c1.text_input("아이 이름", st.session_state.story_config.child_name)
        st.session_state.story_config.partner_name = c2.text_input("짝꿍 이름 (친구, 인형 등)", st.session_state.story_config.partner_name)
        
        c3, c4, c5 = st.columns([1, 2, 2])
        st.session_state.story_config.age = c3.text_input("나이", st.session_state.story_config.age)
        st.session_state.story_config.genre = c4.selectbox("장르", GENRE_OPTIONS)
        st.session_state.story_config.purpose = c5.selectbox("교육 목적", PURPOSE_OPTIONS)

def process_images(files):
    try:
        api_key = get_api_key()
        llm = LLMService(api_key)
    except Exception as e:
        st.error(f"설정 오류: {e}")
        return

    ph = st.empty()
    with ph.container():
        st.markdown("""
        <div class='loader-overlay'>
            <div style='font-size:4rem; margin-bottom: 20px;'>🔮</div>
            <h2 style='color:#FF9EAA; font-family:"Jua"; font-size: 2.5rem;'>포동이가 사진을 읽고 있어요...</h2>
            <p style='color:#AAA; font-size: 1.2rem; margin-top: 10px;'>잠시만 기다려주세요! (약 30초~1분)</p>
        </div>
        """, unsafe_allow_html=True)
        
        cards = []
        prog = st.progress(0)
        
        for i, f in enumerate(files):
            f.seek(0)
            f_bytes = f.read()
            pil_img = Image.open(io.BytesIO(f_bytes))
            card = llm.generate_story_card(io.BytesIO(f_bytes), st.session_state.story_config)
            if card:
                card.image_key = f"img_{i}_{int(time.time())}"
                st.session_state.image_storage[card.image_key] = pil_img
                cards.append(card)
            prog.progress((i+1)/len(files))
        
        st.session_state.story_cards = cards
        st.session_state.generation_complete = True
    ph.empty()
    st.rerun()

def scene_view():
    idx = st.session_state.page_idx
    cards = st.session_state.story_cards
    if not cards: return st.error("생성된 이야기가 없습니다.")
    
    card = cards[idx]
    b64 = Utils.get_image_base64(st.session_state.image_storage.get(card.image_key))
    
    st.progress((idx + 1) / len(cards))
    st.markdown(f"<div style='text-align:right; color:#AAA; font-size:0.9rem;'>Page {idx+1} / {len(cards)}</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        st.markdown(f"""
        <div class='polaroid-frame'>
            <img src='data:image/jpeg;base64,{b64}' class='polaroid-img'>
            <div class='polaroid-label'>✨ {card.character_name}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='dialogue-box'>
            "{card.dialogue}"
        </div>
        <div style='background:white; padding:20px; border-left:5px solid #A0C4FF; border-radius:0 10px 10px 0; color:#666;'>
            <strong>📖 상황 설명</strong><br>
            {card.story_narration}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    c_prev, c_next = st.columns([1, 4])
    if idx > 0:
        if c_prev.button("⬅️ 이전 페이지"): st.session_state.page_idx -= 1; st.rerun()
    
    if idx < len(cards)-1: 
        if c_next.button("다음 페이지 ➡️"): st.session_state.page_idx += 1; st.rerun()
    else:
        if c_next.button("✨ 동화책 완성하기!", type="primary"): st.session_state.show_final = True; st.rerun()

def final_view():
    if not st.session_state.final_story_text:
        with st.spinner("이야기 조각들을 모아 동화책을 만들고 있어요..."):
            llm = LLMService(get_api_key())
            text = llm.generate_final_story(st.session_state.story_cards, st.session_state.story_config)
            audio = AudioService.create(text)
            st.session_state.final_story_text = text; st.session_state.final_audio_data = audio; st.rerun()
            
    st.markdown("<h2 style='text-align:center; color:#FF9EAA; font-size:2.5rem;'>📕 나만의 동화책이 완성되었어요!</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    c1, c2 = st.columns([1.5, 1], gap="large")
    with c1:
        st.markdown(f"""
        <div style='background:white; padding:40px; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.05); line-height:2.2; font-size:1.1rem; border:1px solid #EEE;'>
            {st.session_state.final_story_text.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown("### 🎧 들어보기")
        if st.session_state.final_audio_data: 
            st.audio(st.session_state.final_audio_data, format="audio/mp3")
        
        st.markdown("### 💾 저장하기")
        if st.button("🏠 처음으로 돌아가기"): 
            st.session_state.clear(); st.rerun()

# ==============================================================================
# MAIN ROUTING
# ==============================================================================
def main():
    inject_css()
    AppState.init()

    if not st.session_state.generation_complete:
        if st.session_state.mode is None:
            landing_page()
        else:
            render_config()
            st.markdown("---")
            
            if st.session_state.mode == "upload":
                files = st.file_uploader("사진을 올려주세요 (여러 장 가능)", accept_multiple_files=True)
                if files:
                    if st.button("✨ 이야기 만들기 시작!", type="primary"): process_images(files)
                    
            elif st.session_state.mode == "camera":
                captured_images = CameraManager.render_camera_ui()
                if captured_images:
                    process_images(captured_images)
                    
    elif st.session_state.show_final:
        final_view()
    else:
        scene_view()

if __name__ == "__main__":
    main()