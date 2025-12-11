import time
import io
import json
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
        
        /* 기본 설정 */
        .stApp { background: linear-gradient(135deg, #FFFBF8 0%, #FFF5F7 50%, #F0F7FF 100%); font-family: 'Gowun Dodum', sans-serif; }
        h1, h2, h3, h4 { font-family: 'Jua', sans-serif; color: #3A3A3A; }
        .block-container { padding-top: 2rem !important; }

        /* ================= [랜딩 페이지] 카드 버튼 스타일 ================= */
        /* 투명 버튼 안에 카드 HTML을 넣어서 클릭하게 만드는 트릭 */
        div[data-testid="stButton"] button[key^="btn_landing"] {
            background-color: white !important;
            border: 2px solid white !important;
            border-radius: 20px !important;
            height: 280px !important;
            width: 100% !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05) !important;
            display: flex !important; flex-direction: column !important;
            justify-content: center !important; align-items: center !important;
            white-space: pre-wrap !important; /* 줄바꿈 허용 */
            color: #4A4A4A !important; font-family: 'Jua' !important; font-size: 1.3rem !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stButton"] button[key^="btn_landing"]:hover {
            transform: translateY(-7px) !important;
            box-shadow: 0 15px 35px rgba(255, 158, 170, 0.2) !important;
            border-color: var(--primary) !important;
            background-color: #FFF0F5 !important;
            color: #FF9EAA !important;
        }

        /* ================= [마지막 화면] 동화책 스타일 ================= */
        .book-container {
            background-color: white;
            padding: 50px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            border-left: 10px solid #FF9EAA; /* 책등 느낌 */
            margin-bottom: 30px;
        }
        .book-title {
            font-family: 'Jua', sans-serif;
            font-size: 2.2rem;
            color: #FF9EAA;
            margin-bottom: 10px;
            text-align: center;
        }
        .book-body {
            font-family: 'Gowun Dodum', sans-serif;
            font-size: 1.15rem;
            line-height: 2.0;
            color: #555;
            white-space: pre-line; /* 줄바꿈 반영 */
            text-align: justify;
        }

        /* 일반 버튼 스타일 */
        div[data-testid="stButton"] button:not([key^="btn_landing"]) { 
            border-radius: 12px !important; background: linear-gradient(45deg, var(--primary), #FF8495) !important; 
            color: white !important; font-family: 'Jua' !important; border: none !important; 
            height: 54px !important; font-size: 1.2rem !important; width: 100% !important;
            box-shadow: 0 4px 15px rgba(255, 158, 170, 0.3) !important;
        }
        div[data-testid="stButton"] button:not([key^="btn_landing"]):hover { transform: translateY(-3px); }

        /* 기타 UI */
        .polaroid-frame { background: white; padding: 15px 15px 50px 15px; border: 1px solid #EEE; box-shadow: 0 8px 20px rgba(0,0,0,0.05); border-radius: 4px; }
        .polaroid-img { width: 100%; border-radius: 2px; border: 1px solid #F0F0F0; }
        .dialogue-box { background: #FFFBE6; border: 2px solid #FFF5C4; border-radius: 20px 20px 20px 0; padding: 25px; font-family: 'Jua'; font-size: 1.3rem; color: #5D4037; }
        .loader-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255, 255, 255, 0.95); z-index: 9999; display: flex; flex-direction: column; justify-content: center; align-items: center; }
        
        /* Streamlit UI 숨기기 */
        div[data-testid="stToolbar"], div[data-testid="stDecoration"], div[data-testid="stStatusWidget"], #MainMenu, header, footer { display: none !important; }
        .viewerBadge_container__1QSob, [class*="viewerBadge"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

class AppState:
    @staticmethod
    def init():
        keys = { "mode": None, "page_idx": 0, "show_final": False, "story_cards": [], "final_story_text": None, "final_audio_data": None, "generation_complete": False, "image_storage": {} }
        for k, v in keys.items():
            if k not in st.session_state: st.session_state[k] = v
        if "story_config" not in st.session_state: st.session_state.story_config = StoryConfig()

# ==============================================================================
# UI PAGES
# ==============================================================================
def landing_page():
    st.markdown("<div style='height: 8vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center; font-size:4.5rem; color:#FF9EAA; text-shadow: 3px 3px 0 #FFF; margin-bottom: 10px;'>🧸 포동 PHODONG</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888; font-size:1.3rem; margin-bottom:70px;'>우리 아이를 위한 세상에 하나뿐인 AI 동화책</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2.2, 1])
    with c2:
        col_up, col_cam = st.columns(2, gap="large")
        # 카드 버튼 (줄바꿈 \n 활용)
        with col_up:
            if st.button("📂\n\n\n앨범 업로드\n\n찍어둔 사진으로 만들어요", key="btn_landing_up"):
                st.session_state.mode = "upload"; st.rerun()
        with col_cam:
            if st.button("📸\n\n\n카메라 촬영\n\n지금 바로 찍어서 만들어요", key="btn_landing_cam"):
                st.session_state.mode = "camera"; st.rerun()

def render_config():
    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("🏠 처음으로"): st.session_state.mode = None; st.session_state.camera_captures = []; st.rerun()
    st.markdown("### ⚙️ 어떤 이야기를 만들어볼까요?")
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
    except Exception as e: st.error(f"설정 오류: {e}"); return

    ph = st.empty()
    with ph.container():
        st.markdown("<div class='loader-overlay'><div style='font-size:4rem; margin-bottom:20px;'>🔮</div><h2 style='color:#FF9EAA; font-family:Jua;'>포동이가 사진을 읽고 있어요...</h2><p style='color:#AAA;'>잠시만 기다려주세요!</p></div>", unsafe_allow_html=True)
        cards = []; prog = st.progress(0)
        for i, f in enumerate(files):
            f.seek(0); f_bytes = f.read(); pil_img = Image.open(io.BytesIO(f_bytes))
            card = llm.generate_story_card(io.BytesIO(f_bytes), st.session_state.story_config)
            if card:
                card.image_key = f"img_{i}_{int(time.time())}"
                st.session_state.image_storage[card.image_key] = pil_img
                cards.append(card)
            prog.progress((i+1)/len(files))
        st.session_state.story_cards = cards
        st.session_state.generation_complete = True
    ph.empty(); st.rerun()

def scene_view():
    idx = st.session_state.page_idx
    cards = st.session_state.story_cards
    if not cards: return st.error("생성된 이야기가 없습니다.")
    card = cards[idx]
    b64 = Utils.get_image_base64(st.session_state.image_storage.get(card.image_key))
    st.progress((idx+1)/len(cards))
    st.markdown(f"<div style='text-align:right; color:#AAA; font-size:0.9rem;'>Page {idx+1} / {len(cards)}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1], gap="large")
    with c1: st.markdown(f"<div class='polaroid-frame'><img src='data:image/jpeg;base64,{b64}' class='polaroid-img'><div class='polaroid-label'>✨ {card.character_name}</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='dialogue-box'>\"{card.dialogue}\"</div><div style='background:white; padding:20px; border-left:5px solid #A0C4FF; border-radius:0 10px 10px 0; color:#666;'><strong>📖 상황 설명</strong><br>{card.story_narration}</div>", unsafe_allow_html=True)
    st.markdown("---")
    c_prev, c_next = st.columns([1, 4])
    if idx > 0 and c_prev.button("⬅️ 이전 페이지"): st.session_state.page_idx -= 1; st.rerun()
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
    
    # [핵심] JSON 파싱 및 예쁜 UI 렌더링
    raw_text = st.session_state.final_story_text
    title = "나만의 동화책"
    body = raw_text

    try:
        data = json.loads(raw_text)
        if isinstance(data, list) and len(data) > 0: data = data[0]
        if isinstance(data, dict):
            title = data.get("title", "제목 없는 동화")
            body = data.get("story", raw_text)
    except:
        # JSON이 아닐 경우 대비 (제목 추출)
        lines = raw_text.strip().split('\n')
        if len(lines) > 1:
            title = lines[0].replace("#", "").strip()
            body = "\n".join(lines[1:])

    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#FF9EAA; font-size:2.5rem; margin-bottom:30px;'>🎉 동화책이 완성되었어요!</h2>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1.5, 1], gap="large")
    with c1:
        # 책 모양 컨테이너
        st.markdown(f"""
        <div class="book-container">
            <div class="book-title">{title}</div>
            <hr style="border: 0; border-top: 1px dashed #FF9EAA; margin: 20px 0;">
            <div class="book-body">{body}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown("### 🎧 들어보기")
        if st.session_state.final_audio_data: st.audio(st.session_state.final_audio_data, format="audio/mp3")
        st.markdown("### 💾 저장하기")
        if st.button("🏠 처음으로 돌아가기"): st.session_state.clear(); st.rerun()

def main():
    inject_css()
    AppState.init()
    if not st.session_state.generation_complete:
        if st.session_state.mode is None: landing_page()
        else:
            render_config(); st.markdown("---")
            if st.session_state.mode == "upload":
                files = st.file_uploader("사진을 올려주세요", accept_multiple_files=True)
                if files and st.button("✨ 이야기 만들기 시작!", type="primary"): process_images(files)
            elif st.session_state.mode == "camera":
                captured_images = CameraManager.render_camera_ui()
                if captured_images: process_images(captured_images)
    elif st.session_state.show_final: final_view()
    else: scene_view()

if __name__ == "__main__":
    main()