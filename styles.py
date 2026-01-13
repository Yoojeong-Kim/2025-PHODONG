import streamlit as st

# CSS 코드를 변수에 담아둡니다.
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
    .block-container { padding-top: 2rem !important; padding-bottom: 5rem !important; max-width: 1280px; }
    header, footer, [data-testid="stToolbar"] { visibility: hidden; }

    /* Typography */
    h1, h2, h3, .font-heading { font-family: 'Jua', sans-serif !important; letter-spacing: -0.01em; color: var(--text-title); text-align: left; }
    p, div, span, label, li { font-family: 'Gowun Dodum', sans-serif; font-size: 1.15rem; line-height: 1.8; color: var(--text-body); text-align: left; word-break: keep-all; }

    /* === 🧸 LANDING PAGE (메인 타이틀 수정됨) === */
    /* [수정] h1 태그 제한을 풀고 클래스 자체에 강력하게 적용 */
    .landing-title {
        font-family: 'Jua', sans-serif !important;
        color: #FF9EAA !important;
        font-size: clamp(2.8rem, 7vw, 5rem) !important; /* 크기 살짝 더 키움 */
        font-weight: normal; /* Jua체는 굵기 조절 불필요 */
        text-align: center;
        margin-bottom: 20px;
        line-height: 1.2;
        word-break: keep-all;
        text-shadow: 3px 3px 0px #FFF0F5, 4px 4px 5px rgba(0,0,0,0.05);
        display: block; /* 블록 요소로 강제 */
    }

    .landing-subtitle {
        font-size: clamp(1.1rem, 3vw, 1.5rem) !important;
        color: #777;
        margin-bottom: 40px;
        font-weight: bold;
        text-align: center;
        line-height: 1.6;
    }

    /* === 📖 STORY VIEWER (디자인 실종 해결) === */
    
    /* 1. 폴라로이드 */
    .polaroid-frame {
        background: white !important;
        padding: 20px 20px 40px 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        transform: rotate(-2deg);
        transition: transform 0.3s;
        border-radius: 4px;
        margin-bottom: 20px;
        border: 1px solid #eee; /* 경계선 추가 */
    }
    .polaroid-frame:hover { transform: rotate(0deg) scale(1.02); }
    .polaroid-img { width: 100%; height: auto; border: 2px solid #F0F0F0; margin-bottom: 15px; }
    .polaroid-label { font-family: 'Jua', sans-serif; font-size: 1.2rem; color: #555; text-align: center; }

    /* 2. 캐릭터 프로필 (민트색) */
    .profile-group {
        background-color: #F0FFF9 !important; /* 배경색 강제 적용 */
        border: 3px solid #B5EAD7 !important;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        margin-top: 20px;
    }
    .badge-pill {
        display: inline-block; padding: 6px 12px; border-radius: 50px;
        font-family: 'Jua', sans-serif;
        font-size: clamp(0.9rem, 2vw, 1.1rem) !important;
        margin-right: 5px; margin-bottom: 5px;
        background: white; /* 기본 흰 배경 */
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .badge-pink { background: #FFF0F5 !important; color: #FF9EAA !important; border: 2px solid #FF9EAA !important; }
    .badge-yellow { background: #FFFBE6 !important; color: #FFD580 !important; border: 2px solid #FFD580 !important; }

    /* 3. 대사 박스 (노란색) */
    .dialogue-box {
        background-color: #FFFBE6 !important; /* 배경색 강제 적용 */
        border: 4px solid #FFE082 !important;
        border-radius: 25px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        position: relative;
        margin-bottom: 20px;
        z-index: 1; /* 앞으로 가져오기 */
    }
    .dialogue-text {
        font-family: 'Jua', sans-serif;
        font-size: clamp(1.2rem, 2.5vw, 1.5rem) !important;
        color: #5D4037;
        line-height: 1.5;
        text-align: center;
    }

    /* 4. 상황 설명 (파란색) */
    .context-box {
        background-color: #F0F7FF !important;
        border: 3px solid #A0C4FF !important;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        font-size: clamp(1rem, 1.8vw, 1.15rem) !important;
        line-height: 1.7;
        color: #555;
    }

    /* === UI ELEMENTS === */
    .step-container { display: flex; gap: 20px; margin-top: 40px; }
    .step-item { flex: 1; background: white; padding: 25px; border-radius: 16px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); border-top: 5px solid #EEE; }
    .step-title { font-family: 'Jua'; font-size: 1.2rem; margin: 15px 0 5px 0; color: #3A3A3A; }
    .step-desc { font-size: 1rem; color: #888; }

    .stButton > button {
        width: 100%; height: 54px; border-radius: 12px; border: none;
        background: linear-gradient(45deg, #FF9EAA, #FF8495);
        color: white !important; font-family: 'Jua';
        font-size: clamp(1.1rem, 2vw, 1.3rem) !important;
        box-shadow: 0 6px 15px rgba(255, 158, 170, 0.3);
    }
    [data-testid="stFileUploader"] { border: 3px dashed #A0C4FF; border-radius: 24px; padding: 30px; background: #F0F7FF; text-align: center; }

    /* === 📱 MOBILE === */
    @media only screen and (max-width: 768px) {
        .block-container { padding: 1rem 1.2rem 3rem 1.2rem !important; }
        .step-container { flex-direction: column; gap: 10px; }
        .step-item { padding: 15px; display: flex; align-items: center; gap: 15px; }
        .polaroid-frame, .profile-group, .dialogue-box, .context-box { transform: none !important; margin-bottom: 15px; }
        [data-testid="column"] { width: 100% !important; flex: 1 1 auto !important; min-width: unset !important; }
    }
</style>
"""

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

    @staticmethod
    def escape(text: str) -> str:
        import html
        return html.escape(str(text))