# styles.py
import streamlit as st

# CSS 코드를 변수에 담아둡니다. (app.py에서 가져다 쓰기 위함)
# ==============================================================================
# 0. 🎨 CSS 스타일 (전체 반응형 적용 완료)
# ==============================================================================
CSS_STYLE = """
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

    /* === GLOBAL RESET & TYPOGRAPHY === */
    .stApp {
        background-color: var(--bg-base);
        background-image: linear-gradient(135deg, #FFFBF8 0%, #FFF5F7 50%, #F0F7FF 100%);
        color: var(--text-body);
        font-family: 'Gowun Dodum', sans-serif;
        text-align: left !important;
    }
    .block-container { 
        padding-top: 2rem !important; 
        padding-bottom: 5rem !important; 
        max-width: 1280px; 
    }
    header, footer, [data-testid="stToolbar"] { visibility: hidden; }

    /* [전체 폰트 반응형 설정] */
    /* 기본 텍스트: 최소 16px ~ 최대 19px */
    p, div, span, label, li, .stMarkdown { 
        font-family: 'Gowun Dodum', sans-serif; 
        font-size: clamp(1rem, 1.5vw, 1.2rem) !important; 
        line-height: 1.7; 
        color: var(--text-body); 
        word-break: keep-all; 
    }
    
    /* 제목 태그: 화면 비례해서 커짐 */
    h1, h2, h3, .font-heading { 
        font-family: 'Jua', sans-serif; 
        letter-spacing: -0.01em; 
        color: var(--text-title); 
        text-align: left; 
    }

    /* === 🧸 LANDING PAGE (메인 화면) === */
    .landing-hero { 
        padding: 20px 10px; 
        text-align: center;
    }
    
    /* [수정] 메인 타이틀: 통통한 폰트 + 반응형 크기 (2.5rem ~ 4.5rem) */
    .landing-title {
        font-family: 'Jua', sans-serif !important;
        color: #FF9EAA !important;
        font-size: clamp(2.5rem, 6vw, 4.5rem) !important; 
        text-align: center;
        margin-bottom: 15px;
        line-height: 1.3;
        word-break: keep-all;
        text-shadow: 3px 3px 0px #FFF0F5, 4px 4px 5px rgba(0,0,0,0.05); 
    }

    /* [수정] 서브 타이틀: 반응형 크기 (1rem ~ 1.5rem) */
    .landing-subtitle {
        font-size: clamp(1rem, 3vw, 1.5rem) !important; 
        color: #777; 
        margin-bottom: 40px; 
        font-weight: bold;
        text-align: center;
        line-height: 1.5;
    }
    
    /* 3-Step Guide */
    .step-container { display: flex; gap: 20px; margin-top: 20px; }
    .step-item {
        flex: 1; background: white; padding: 20px; border-radius: var(--radius-md);
        box-shadow: var(--shadow-soft); border-top: 5px solid #EEE;
        transition: transform 0.3s;
    }
    .step-item:hover { transform: translateY(-5px); }
    .step-1 { border-color: var(--tertiary); }
    .step-2 { border-color: var(--secondary); }
    .step-3 { border-color: var(--primary); }
    
    /* 단계별 제목/설명 반응형 */
    .step-title { font-family: 'Jua'; font-size: clamp(1.1rem, 2vw, 1.3rem) !important; margin: 10px 0 5px 0; color: var(--text-title); }
    .step-desc { font-size: clamp(0.9rem, 1.5vw, 1rem) !important; color: #888; line-height: 1.4; }

    /* === 📖 STORY VIEWER (동화책 화면) === */

    /* 1. 폴라로이드 프레임 */
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

    /* 2. 캐릭터 프로필 (뱃지) */
    .profile-group {
        background: #F0FFF9; border: 3px solid #B5EAD7; border-radius: var(--radius-md);
        padding: 20px; box-shadow: var(--shadow-soft); margin-top: 20px;
    }
    .badge-pill {
        display: inline-block; padding: 6px 12px; border-radius: 50px;
        font-family: 'Jua', sans-serif; 
        font-size: clamp(0.9rem, 2vw, 1.1rem) !important; /* 뱃지 글씨도 반응형 */
        margin-right: 5px; margin-bottom: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .badge-pink { background: #FFF0F5; color: #FF9EAA; border: 2px solid #FF9EAA; }
    .badge-yellow { background: #FFFBE6; color: #FFD580; border: 2px solid #FFD580; }

    /* 3. 대사 박스 & 지문 박스 */
    .dialogue-box {
        background: #FFFBE6; border: 4px solid #FFE082; border-radius: 25px;
        padding: 25px; box-shadow: var(--shadow-soft); position: relative; margin-bottom: 20px;
    }
    .dialogue-text { 
        font-family: 'Jua', sans-serif; 
        font-size: clamp(1.2rem, 2.5vw, 1.5rem) !important; /* 대사는 좀 더 크게 반응형 */
        color: #5D4037; 
        line-height: 1.5; text-align: center; 
    }

    .context-box {
        background: #F0F7FF; border: 3px solid #A0C4FF; border-radius: var(--radius-md);
        padding: 20px; box-shadow: var(--shadow-soft); 
        font-size: clamp(1rem, 1.8vw, 1.15rem) !important; /* 지문 텍스트 반응형 */
        line-height: 1.7; color: #555;
    }

    /* === UI ELEMENTS === */
    .stButton > button {
        width: 100%; height: 54px; border-radius: 12px; border: none;
        background: linear-gradient(45deg, var(--primary), #FF8495);
        color: white !important; font-family: 'Jua'; 
        font-size: clamp(1.1rem, 2vw, 1.3rem) !important; /* 버튼 글씨 반응형 */
        box-shadow: 0 6px 15px rgba(255, 158, 170, 0.3); transition: all 0.2s;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(255, 158, 170, 0.4); }
    
    [data-testid="stFileUploader"] { border: 3px dashed #A0C4FF; border-radius: var(--radius-lg); padding: 30px 10px; background: #F0F7FF; text-align: center; }
    
    /* Expander 스타일 살짝 수정 */
    .streamlit-expanderHeader {
        font-family: 'Jua', sans-serif;
        font-size: 1.1rem;
        color: #555;
    }

    /* === 📱 모바일 최적화 (레이아웃 조정 위주) === */
    @media only screen and (max-width: 768px) {
        .block-container { 
            padding: 1rem 1rem 3rem 1rem !important; 
        }
        
        /* 모바일에서 단계별 가이드는 세로로 */
        .step-container { flex-direction: column; gap: 10px; }
        .step-item { padding: 15px; display: flex; align-items: center; gap: 15px; text-align: left; }
        .step-title { margin: 0 !important; }
        
        /* 폴라로이드 회전 효과 제거 (공간 절약) */
        .polaroid-frame { transform: none !important; margin-bottom: 15px; }
        
        /* 말풍선 꼬리 위치 조정 (선택사항) */
        .dialogue-box::after { display: none; } /* 모바일엔 공간 좁으니 꼬리 제거 깔끔하게 */
        
        /* 스트림릿 컬럼 강제 100% (세로 배치) */
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