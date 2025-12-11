import time
import io
import streamlit as st
from PIL import Image

# 👇 [변경된 부분] 파일 이름 변경에 따른 import 수정
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
        @import url('[https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&display=swap](https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&display=swap)');
        :root { --bg-base: #FFFBF8; --primary: #FF9EAA; --secondary: #FFD580; --tertiary: #A0C4FF; }
        .stApp { background: linear-gradient(135deg, #FFFBF8 0%, #FFF5F7 50%, #F0F7FF 100%); font-family: 'Gowun Dodum', sans-serif; }
        h1, h2, h3 { font-family: 'Jua', sans-serif; color: #3A3A3A; }
        .stButton>button { border-radius: 12px; background: linear-gradient(45deg, var(--primary), #FF8495); color: white; font-family: 'Jua'; border: none; height: 50px; font-size: 1.2rem; }
        .polaroid-frame { background: white; padding: 15px 15px 50px 15px; border: 1px solid #EEE; box-shadow: 0 8px 20px rgba(0,0,0,0.05); border-radius: 4px; }
        .polaroid-img { width: 100%; border-radius: 2px; border: 1px solid #F0F0F0; }
        .polaroid-label { text-align: center; margin-top: 15px; font-family: 'Jua'; color: #BBB; }
        .dialogue-box { background: #FFFBE6; border: 2px solid #FFF5C4; border-radius: 20px 20px 20px 0; padding: 25px; margin-bottom: 20px; font-family: 'Jua'; font-size: 1.3rem; color: #5D4037; }
        .loader-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: white; z-index: 9999; display: flex; flex-direction: column; justify-content: center; align-items: center; }

        /* 🔥 Streamlit UI 숨기기 (완벽 버전) 🔥 */
        div[data-testid="stToolbar"], div[data-testid="stDecoration"], div[data-testid="stStatusWidget"], #MainMenu, header, footer {
            visibility: hidden; height: 0%; position: fixed;
        }
        .viewerBadge_container__1QSob, [class*="viewerBadge"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

class AppState:
    @staticmethod
    def init():
        if "mode" not in st.session_state: st.session_state.mode = None 
        if "page_idx" not in st.session_state: st.session_state.page_idx = 0
        if "show_final" not in st.session_state: st.session_state.show_final = False
        if "story_config" not in st.session_state: st.session_state.story_config = StoryConfig()
        if "story_cards" not in st.session_state: st.session_state.story_cards = []
        if "final_story_text" not in st.session_state: st.session_state.final_story_text = None
        if "final_audio_data" not in st.session_state: st.session_state.final_audio_data = None
        if "generation_complete" not in st.session_state: st.session_state.generation_complete = False
        if "image_storage" not in st.session_state: st.session_state.image_storage = {}

# ==============================================================================
# UI PAGES
# ==============================================================================
def landing_page():
    st.markdown("<h1 style='text-align:center; font-size:3rem; color:#FF9EAA;'>🧸 포동 PHODONG</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888; margin-bottom:50px;'>아이를 위한 맞춤형 동화책을 만들어보세요</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        col_up, col_cam = st.columns(2, gap="medium")
        with col_up:
            st.markdown("<div style='text-align:center; font-size:3rem;'>📂</div>", unsafe_allow_html=True)
            if st.button("앨범 업로드", use_container_width=True):
                st.session_state.mode = "upload"; st.rerun()
        with col_cam:
            st.markdown("<div style='text-align:center; font-size:3rem;'>📸</div>", unsafe_allow_html=True)
            if st.button("카메라 촬영", use_container_width=True):
                st.session_state.mode = "camera"; st.rerun()

def render_config():
    st.markdown(f"### ⚙️ 설정: {st.session_state.story_config.child_name}")
    with st.expander("설정 수정하기", expanded=True):
        c1, c2 = st.columns(2)
        st.session_state.story_config.child_name = c1.text_input("아이 이름", st.session_state.story_config.child_name)
        st.session_state.story_config.partner_name = c2.text_input("짝꿍 이름", st.session_state.story_config.partner_name)
        st.session_state.story_config.age = c1.text_input("나이", st.session_state.story_config.age)
        st.session_state.story_config.genre = c2.selectbox("장르", GENRE_OPTIONS)
        st.session_state.story_config.purpose = c1.selectbox("목적", PURPOSE_OPTIONS)

def process_images(files):
    try:
        api_key = get_api_key()
        llm = LLMService(api_key)
    except Exception as e:
        st.error(f"API 키 오류: {e}")
        return

    ph = st.empty()
    with ph.container():
        st.markdown("<div class='loader-overlay'><h2>🔮 포동이가 이야기를 짓고 있어요...</h2></div>", unsafe_allow_html=True)
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
    
    st.markdown(f"### Scene {idx+1}")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='polaroid-frame'><img src='data:image/jpeg;base64,{b64}' class='polaroid-img'><div class='polaroid-label'>{card.character_name}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='dialogue-box'>\"{card.dialogue}\"</div>", unsafe_allow_html=True)
        st.info(f"상황: {card.story_narration}")
    
    c_prev, c_next = st.columns([1, 4])
    if idx > 0 and c_prev.button("⬅️ 이전"): st.session_state.page_idx -= 1; st.rerun()
    if idx < len(cards)-1: 
        if c_next.button("다음 ➡️"): st.session_state.page_idx += 1; st.rerun()
    else:
        if c_next.button("✨ 완성하기", type="primary"): st.session_state.show_final = True; st.rerun()

def final_view():
    # 1. 아직 이야기가 없으면 생성 (기존 로직 유지)
    if not st.session_state.final_story_text:
        with st.spinner("책 엮는 중..."):
            llm = LLMService(get_api_key())
            text = llm.generate_final_story(st.session_state.story_cards, st.session_state.story_config)
            audio = AudioService.create(text)
            st.session_state.final_story_text = text
            st.session_state.final_audio_data = audio
            st.rerun()
            
    # 2. [수정됨] JSON 파싱 및 이쁜 디자인 적용
    import json # JSON 처리를 위해 임포트
    
    raw_text = st.session_state.final_story_text
    title = "나만의 동화책"
    body = raw_text

    # JSON 파싱 시도 (제목과 본문 분리)
    try:
        data = json.loads(raw_text)
        if isinstance(data, list) and len(data) > 0: data = data[0]
        if isinstance(data, dict):
            title = data.get("title", "제목 없는 동화")
            body = data.get("story", raw_text)
    except:
        # JSON이 아닐 경우 첫 줄을 제목으로 사용
        lines = raw_text.strip().split('\n')
        if len(lines) > 1:
            title = lines[0].replace("#", "").strip()
            body = "\n".join(lines[1:])

    # 3. 화면 렌더링
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#FF9EAA; font-size:2.5rem; margin-bottom:30px;'>🎉 동화책이 완성되었어요!</h2>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1.5, 1], gap="large")
    
    # [왼쪽] 책 모양 디자인 (인라인 스타일 사용으로 CSS 수정 없이 적용)
    with c1:
        st.markdown(f"""
        <div style="background-color: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.08); border-left: 10px solid #FF9EAA;">
            <div style="font-family: 'Jua', sans-serif; font-size: 2.0rem; color: #FF9EAA; text-align: center; margin-bottom: 20px;">
                {title}
            </div>
            <hr style="border: 0; border-top: 1px dashed #FF9EAA; margin-bottom: 20px;">
            <div style="font-family: 'Gowun Dodum', sans-serif; font-size: 1.15rem; line-height: 2.0; color: #555; white-space: pre-wrap; text-align: justify;">
                {body}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # [오른쪽] 오디오 및 버튼
    with c2:
        st.markdown("### 🎧 들어보기")
        if st.session_state.final_audio_data: 
            st.audio(st.session_state.final_audio_data, format="audio/mp3")
        
        st.markdown("### 💾 저장하기")
        # 다운로드 버튼 기능 추가 (원하시면 HTML 다운로드 등 추가 가능)
        if st.button("🏠 처음으로"): 
            st.session_state.clear()
            st.rerun()

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
            if st.button("🏠 홈으로"): st.session_state.mode = None; st.rerun()
            render_config()
            st.markdown("---")
            
            # [핵심] 모드에 따른 분기 처리
            if st.session_state.mode == "upload":
                files = st.file_uploader("사진 업로드", accept_multiple_files=True)
                if files and st.button("만들기", type="primary"): process_images(files)
                    
            elif st.session_state.mode == "camera":
                # 👇 변경된 모듈에서 호출
                captured_images = CameraManager.render_camera_ui()
                if captured_images:
                    process_images(captured_images)
                    
    elif st.session_state.show_final:
        final_view()
    else:
        scene_view()

if __name__ == "__main__":
    main()