import streamlit as st
import re

# ==============================================================================
# 🎨 VECTOR ARTWORK (공통 아이콘 리소스)
# ==============================================================================
class ArtWork:
    """모든 페이지에서 공통으로 사용하는 SVG 아이콘 모음"""
    
    @staticmethod
    def get_bear(size=100):
        return f"""
        <svg width="{size}" height="{size}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="55" r="35" fill="#D6B898"/>
            <circle cx="35" cy="25" r="12" fill="#D6B898"/>
            <circle cx="65" cy="25" r="12" fill="#D6B898"/>
            <circle cx="35" cy="25" r="6" fill="#EAC7A8"/>
            <circle cx="65" cy="25" r="6" fill="#EAC7A8"/>
            <ellipse cx="50" cy="60" rx="14" ry="10" fill="#FFF0F5"/>
            <circle cx="50" cy="56" r="4" fill="#5D4037"/>
            <circle cx="42" cy="48" r="3" fill="#333"/>
            <circle cx="58" cy="48" r="3" fill="#333"/>
            <path d="M50 60V65" stroke="#5D4037" stroke-width="2" stroke-linecap="round"/>
            <path d="M46 65C46 65 48 68 50 68C52 68 54 65 54 65" stroke="#5D4037" stroke-width="2" stroke-linecap="round"/>
        </svg>
        """

    @staticmethod
    def get_book_cover(size=60):
        return f"""
        <svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="10" y="8" width="44" height="48" rx="4" fill="#FF9EAA"/>
            <rect x="14" y="8" width="6" height="48" fill="#FF7B8E"/>
            <rect x="24" y="18" width="26" height="4" rx="2" fill="#FFF5F7"/>
            <rect x="24" y="26" width="18" height="4" rx="2" fill="#FFF5F7"/>
            <circle cx="36" cy="42" r="8" fill="#FFD580"/>
        </svg>
        """
    
    @staticmethod
    def get_folder(size=40):
        return f"""
        <svg width="{size}" height="{size}" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M36 12H20L16 8H4C1.8 8 0 9.8 0 12V32C0 34.2 1.8 36 4 36H36C38.2 36 40 34.2 40 32V16C40 13.8 38.2 12 36 12Z" fill="#A0C4FF"/>
            <path d="M36 16H4V32H36V16Z" fill="#E3F2FD"/>
        </svg>
        """

    @staticmethod
    def get_camera(size=200):
        """이미지가 없을 때 보여주는 기본 카메라 아이콘"""
        return f"""
        <svg width="100%" height="100%" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="200" height="200" fill="#F8F9FA"/>
            <rect x="50" y="60" width="100" height="80" rx="12" fill="#A0C4FF"/>
            <circle cx="100" cy="100" r="30" fill="#FFFFFF" stroke="#89C4F4" stroke-width="6"/>
            <circle cx="100" cy="100" r="15" fill="#FFD580"/>
            <rect x="120" y="50" width="20" height="10" rx="3" fill="#89C4F4"/>
            <text x="100" y="175" font-family="'Jua', sans-serif" font-size="16" fill="#89C4F4" text-anchor="middle">사진이 없어요!</text>
        </svg>
        """

    @staticmethod
    def get_camera_lens(size=60):
        """라이브 페이지용 카메라 렌즈 아이콘"""
        return f"""
        <svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="32" cy="32" r="30" fill="#FF9EAA"/> <circle cx="32" cy="32" r="24" fill="#333"/>
            <circle cx="32" cy="32" r="12" fill="#111" stroke="#555" stroke-width="2"/>
            <circle cx="38" cy="26" r="4" fill="white" opacity="0.6"/>
        </svg>
        """

# ==============================================================================
# 🎨 DESIGN SYSTEM (CSS ENGINE)
# ==============================================================================
class DesignSystem:
    """전체 앱의 스타일(폰트, 색상, 레이아웃)을 정의하는 CSS 클래스"""
    @staticmethod
    def inject_css():
        st.markdown("""
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

            /* === NEW LANDING PAGE LAYOUT (Rich 2-Column) === */
            .landing-hero { padding: 20px; }
            .landing-title {
                font-size: 4rem; color: var(--primary); margin-bottom: 15px; font-family: 'Jua';
                text-shadow: 2px 2px 0px #FFF0F5;
            }
            .landing-subtitle {
                font-size: 1.4rem; color: #777; margin-bottom: 50px; font-weight: bold;
            }
            
            /* 3-Step Guide */
            .step-container { display: flex; gap: 20px; margin-top: 40px; }
            .step-item {
                flex: 1; background: white; padding: 25px; border-radius: var(--radius-md);
                box-shadow: var(--shadow-soft); border-top: 5px solid #EEE;
                transition: transform 0.3s;
            }
            .step-item:hover { transform: translateY(-5px); }
            .step-1 { border-color: var(--tertiary); }
            .step-2 { border-color: var(--secondary); }
            .step-3 { border-color: var(--primary); }
            .step-title { font-family: 'Jua'; font-size: 1.2rem; margin: 15px 0 10px 0; color: var(--text-title); }
            .step-desc { font-size: 1rem; color: #888; line-height: 1.5; }

            /* Landing Action Section */
            .landing-action {
                background: white; padding: 50px; border-radius: var(--radius-lg);
                box-shadow: 0 20px 60px rgba(0,0,0,0.08); border: 4px solid #FFF;
                outline: 2px solid var(--primary-soft); height: 100%;
                display: flex; flex-direction: column; justify-content: center;
                text-align: center;
            }
            .action-header { font-family: 'Jua'; font-size: 1.8rem; color: var(--primary); margin-bottom: 20px; text-align: center; }

            /* === BUTTONS & UPLOADER === */
            .stButton > button {
                width: 100%; height: 54px; border-radius: 12px; border: none;
                background: linear-gradient(45deg, var(--primary), #FF8495);
                color: white !important; font-family: 'Jua'; font-size: 1.25rem;
                box-shadow: 0 6px 15px rgba(255, 158, 170, 0.3); transition: all 0.2s; text-align: center !important;
            }
            .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(255, 158, 170, 0.4); }
            [data-testid="stFileUploader"] {
                border: 3px dashed #A0C4FF; border-radius: var(--radius-lg);
                padding: 50px 30px; background: #F0F7FF; text-align: center;
            }
            /* 카메라 입력 테두리 */
            [data-testid="stCameraInput"] {
                border: 4px solid var(--primary);
                border-radius: var(--radius-lg);
                padding: 10px;
                background: white;
                box-shadow: var(--shadow-soft);
            }
            
            /* Custom Container for Content (Live/Upload Page) */
            .content-box {
                background: white; padding: 30px; border-radius: var(--radius-lg);
                box-shadow: var(--shadow-soft); border: 2px solid #FFF0F5;
                margin-bottom: 20px;
            }

            /* === 📱 모바일 전용 스타일 (화면 너비 768px 이하) === */
            /* 주의: 이 코드는 반드시 <style> 태그 안쪽에 있어야 합니다! */
            @media only screen and (max-width: 768px) {
                
                /* 1. 전체 여백 줄이기 */
                .block-container {
                    padding-top: 1rem !important;
                    padding-bottom: 3rem !important;
                    padding-left: 1rem !important;
                    padding-right: 1rem !important;
                }

                /* 2. 제목 폰트 크기 축소 */
                .landing-title {
                    font-size: 2.5rem !important;
                    text-align: center;
                }
                .landing-subtitle {
                    font-size: 1.1rem !important;
                    text-align: center;
                    margin-bottom: 20px !important;
                }

                /* 3. 단계별 가이드 세로 배치 */
                .step-container {
                    flex-direction: column;
                    gap: 10px;
                    margin-top: 20px;
                }
                .step-item {
                    padding: 15px;
                }

                /* 4. 입력 폼 박스 스타일 단순화 */
                .landing-action {
                    padding: 20px !important;
                    border: 2px solid var(--primary-soft);
                    box-shadow: none;
                }

                /* 5. 버튼 터치 영역 확대 */
                .stButton > button {
                    height: 60px !important;
                    font-size: 1.1rem !important;
                }

                /* 6. 폴라로이드 및 결과 카드 최적화 */
                .polaroid-frame, .result-card, .content-box {
                    padding: 15px !important;
                }
                
                /* 7. 컬럼 강제 조정 (100% 너비) */
                [data-testid="column"] {
                    width: 100% !important;
                    flex: 1 1 auto !important;
                    min-width: unset !important;
                }
            }
        </style>
        """, unsafe_allow_html=True)

class Utils:
    @staticmethod
    def clean_html(html_str: str) -> str:
        return re.sub(r'\s+', ' ', html_str).strip()