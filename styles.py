# styles.py
import streamlit as st

# CSS 코드를 변수에 담아둡니다. (app.py에서 가져다 쓰기 위함)
CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&display=swap');

    :root {
        --bg-base: #FFFBF8;
        --surface: #FFFFFF;
        --primary: #FF9EAA;        /* 핑크 */
        --primary-soft: #FFF0F5;
        --secondary: #FFD580;      /* 옐로우 */
        --secondary-soft: #FFFBE6;
        --tertiary: #A0C4FF;       /* 블루 */
        --tertiary-soft: #F0F7FF;
        --quaternary: #B5EAD7;     /* 민트 */
        --quaternary-soft: #F0FFF9;
        --text-title: #3A3A3A;
        --text-body: #555555;
        --shadow-soft: 0 10px 40px rgba(255, 158, 170, 0.1);
        --radius-lg: 24px;
        --radius-md: 16px;
    }

    /* === GLOBAL RESET === */
    .stApp {
        background-color: var(--bg-base);
        background-image: linear-gradient(135deg, #FFFBF8 0%, #FFF5F7 50%, #F0F7FF 100%);
        color: var(--text-body);
        font-family: 'Gowun Dodum', sans-serif;
        text-align: left !important;
    }
    .block-container { padding-top: 3rem !important; padding-bottom: 5rem !important; max-width: 1280px; }
    header, footer, [data-testid="stToolbar"] { visibility: hidden; }

    /* Typography */
    h1, h2, h3, .font-heading { font-family: 'Jua', sans-serif; letter-spacing: -0.01em; color: var(--text-title); text-align: left; }
    p, div, span, label, li { font-family: 'Gowun Dodum', sans-serif; font-size: 1.15rem; line-height: 1.8; color: var(--text-body); text-align: left; word-break: keep-all; }

    /* === 🌟 핵심 디자인 컴포넌트 === */
    .polaroid-frame {
        background: white;
        padding: 20px 20px 40px 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        transform: rotate(-2deg);
        transition: transform 0.3s;
        border-radius: 4px;
        margin-bottom: 20px;
    }
    .polaroid-frame:hover { transform: rotate(0deg) scale(1.02); }
    .polaroid-img { width: 100%; height: auto; border: 2px solid #F0F0F0; margin-bottom: 15px; }
    .polaroid-label { font-family: 'Jua', sans-serif; font-size: 1.2rem; color: #555; text-align: center; }

    .profile-group {
        background: #F0FFF9; border: 3px solid #B5EAD7; border-radius: var(--radius-md);
        padding: 25px; box-shadow: var(--shadow-soft); margin-top: 20px;
    }
    .badge-pill {
        display: inline-block; padding: 6px 15px; border-radius: 50px;
        font-family: 'Jua', sans-serif; font-size: 1.05rem; margin-right: 5px; margin-bottom: 5px;
    }
    .badge-pink { background: #FFF0F5; color: #FF9EAA; border: 2px solid #FF9EAA; }
    .badge-yellow { background: #FFFBE6; color: #FFD580; border: 2px solid #FFD580; }

    .dialogue-box {
        background: #FFFBE6; border: 4px solid #FFE082; border-radius: 25px;
        padding: 30px; box-shadow: var(--shadow-soft); position: relative; margin-bottom: 30px;
    }
    .dialogue-text { font-family: 'Jua', sans-serif; font-size: 1.4rem; color: #5D4037; line-height: 1.5; text-align: center; }

    .context-box {
        background: #F0F7FF; border: 3px solid #A0C4FF; border-radius: var(--radius-md);
        padding: 25px; box-shadow: var(--shadow-soft); font-size: 1.1rem; line-height: 1.7; color: #555;
    }

    /* === LANDING PAGE === */
    .landing-hero { padding: 20px; }
    .landing-title { font-size: 4rem; color: var(--primary); margin-bottom: 15px; font-family: 'Jua'; text-shadow: 2px 2px 0px #FFF0F5; }
    .landing-subtitle { font-size: 1.4rem; color: #777; margin-bottom: 50px; font-weight: bold; }
    
    .step-container { display: flex; gap: 20px; margin-top: 40px; }
    .step-item { flex: 1; background: white; padding: 25px; border-radius: var(--radius-md); box-shadow: var(--shadow-soft); border-top: 5px solid #EEE; }
    .step-title { font-family: 'Jua'; font-size: 1.2rem; margin: 15px 0 10px 0; color: var(--text-title); }
    .step-desc { font-size: 1rem; color: #888; line-height: 1.5; }

    .landing-action {
        background: white; padding: 50px; border-radius: var(--radius-lg);
        box-shadow: 0 20px 60px rgba(0,0,0,0.08); border: 4px solid #FFF;
        outline: 2px solid var(--primary-soft); height: 100%;
        display: flex; flex-direction: column; justify-content: center; text-align: center;
    }
    .action-header { font-family: 'Jua'; font-size: 1.8rem; color: var(--primary); margin-bottom: 20px; text-align: center; }

    /* === BUTTONS & INPUTS === */
    .stButton > button {
        width: 100%; height: 54px; border-radius: 12px; border: none;
        background: linear-gradient(45deg, var(--primary), #FF8495);
        color: white !important; font-family: 'Jua'; font-size: 1.25rem;
        box-shadow: 0 6px 15px rgba(255, 158, 170, 0.3); transition: all 0.2s;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(255, 158, 170, 0.4); }
    [data-testid="stFileUploader"] { border: 3px dashed #A0C4FF; border-radius: var(--radius-lg); padding: 30px; background: #F0F7FF; text-align: center; }
    .content-box { background: white; padding: 30px; border-radius: var(--radius-lg); box-shadow: var(--shadow-soft); border: 2px solid #FFF0F5; margin-bottom: 20px; }

    /* === 📱 모바일 최적화 === */
    @media only screen and (max-width: 768px) {
        .block-container { padding: 1rem 1.2rem 3rem 1.2rem !important; }
        .landing-title { font-size: clamp(2rem, 6vw, 3rem) !important; text-align: center; line-height: 1.3; word-break: keep-all; margin-bottom: 10px !important; }
        .landing-subtitle { font-size: 1rem !important; text-align: center; line-height: 1.6; word-break: keep-all; margin-bottom: 30px !important; }
        .landing-action { padding: 25px 20px !important; height: auto !important; border-radius: 20px !important; margin-top: 10px; box-shadow: none; border: 2px solid var(--primary-soft); }
        .action-header { font-size: 1.4rem !important; margin-bottom: 15px !important; word-break: keep-all; }
        .step-container { flex-direction: column; gap: 12px; margin-top: 10px; }
        .step-item { padding: 15px; display: flex; align-items: center; gap: 15px; text-align: left; }
        .step-title { margin: 0 !important; font-size: 1.1rem !important; }
        .step-desc { margin: 0 !important; font-size: 0.9rem !important; }
        .stButton > button { height: 56px !important; font-size: 1.1rem !important; }
        .polaroid-frame, .profile-group, .dialogue-box, .context-box { padding: 15px !important; transform: none !important; margin-top: 15px !important; margin-bottom: 15px !important; }
        [data-testid="column"] { width: 100% !important; flex: 1 1 auto !important; min-width: unset !important; }
    }
</style>
"""

# 아이콘 관련 클래스
class ArtWork:
    @staticmethod
    def get_bear(size=100):
        return f"""<svg width="{size}" height="{size}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="55" r="35" fill="#D6B898"/><circle cx="35" cy="25" r="12" fill="#D6B898"/><circle cx="65" cy="25" r="12" fill="#D6B898"/><circle cx="35" cy="25" r="6" fill="#EAC7A8"/><circle cx="65" cy="25" r="6" fill="#EAC7A8"/><ellipse cx="50" cy="60" rx="14" ry="10" fill="#FFF0F5"/><circle cx="50" cy="56" r="4" fill="#5D4037"/><circle cx="42" cy="48" r="3" fill="#333"/><circle cx="58" cy="48" r="3" fill="#333"/><path d="M50 60V65" stroke="#5D4037" stroke-width="2" stroke-linecap="round"/><path d="M46 65C46 65 48 68 50 68C52 68 54 65 54 65" stroke="#5D4037" stroke-width="2" stroke-linecap="round"/></svg>"""

    @staticmethod
    def get_book_cover(size=60):
        return f"""<svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="10" y="8" width="44" height="48" rx="4" fill="#FF9EAA"/><rect x="14" y="8" width="6" height="48" fill="#FF7B8E"/><rect x="24" y="18" width="26" height="4" rx="2" fill="#FFF5F7"/><rect x="24" y="26" width="18" height="4" rx="2" fill="#FFF5F7"/><circle cx="36" cy="42" r="8" fill="#FFD580"/></svg>"""
    
    @staticmethod
    def get_folder(size=40):
        return f"""<svg width="{size}" height="{size}" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M36 12H20L16 8H4C1.8 8 0 9.8 0 12V32C0 34.2 1.8 36 4 36H36C38.2 36 40 34.2 40 32V16C40 13.8 38.2 12 36 12Z" fill="#A0C4FF"/><path d="M36 16H4V32H36V16Z" fill="#E3F2FD"/></svg>"""

class Utils:
    @staticmethod
    def clean_html(html_str: str) -> str:
        import re
        return re.sub(r'\s+', ' ', html_str).strip()