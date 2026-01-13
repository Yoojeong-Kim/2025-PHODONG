import streamlit as st
import styles  # styles.py에 정의된 디자인/아이콘 모듈 임포트

# ==============================================================================
# [필수 1] 페이지 기본 설정
# ==============================================================================
st.set_page_config(
    page_title="포동 PHODONG",
    page_icon="🧸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# [필수 2] 메인 앱 구조
# styles.py를 활용하여 디자인 코드를 직접 작성하지 않고 호출만 합니다.
# ==============================================================================

def main():
    # 1. 스타일 주입 (앱 실행 시 가장 먼저 호출)
    styles.DesignSystem.inject_css()

    # 2. 헤더 섹션 (로고 및 타이틀)
    # styles.ArtWork에서 곰돌이 아이콘을 가져옵니다.
    bear = styles.ArtWork.get_bear(45)
    c1, c2 = st.columns([0.8, 11.2])
    with c1: st.markdown(f"<div>{bear}</div>", unsafe_allow_html=True)
    with c2: 
        st.markdown(styles.Utils.clean_html("""
            <div style="display:flex; align-items:center; height:100%;">
                <h3 class='font-heading' style='color:#FF9EAA; margin:0; font-size:1.8rem;'>포동 PHODONG</h3>
            </div>
        """), unsafe_allow_html=True)
    st.markdown("<hr style='margin: 15px 0 40px 0; border:0; border-top:2px solid #F0F0F0;'>", unsafe_allow_html=True)

    # ==========================================================================
    # [수정 구간] 여기부터 사용자님의 기존 '구현 로직'을 넣으세요.
    # ==========================================================================
    
    # 예시: 메인 콘텐츠 영역 (2컬럼 레이아웃)
    left_col, right_col = st.columns([1.3, 1], gap="large")

    with left_col:
        # [디자인 적용] 제목 및 설명
        st.markdown("""
            <h1 class="landing-title">나의 웹사이트 제목</h1>
            <p class="landing-subtitle">여기에 부제목이나 설명을 적으세요.</p>
        """, unsafe_allow_html=True)
        
        # [디자인 적용] 3단계 가이드 (styles.ArtWork 아이콘 활용)
        folder_icon = styles.ArtWork.get_folder(40)
        bear_icon = styles.ArtWork.get_bear(40)
        book_icon = styles.ArtWork.get_book_cover(40)
        
        st.markdown(styles.Utils.clean_html(f"""
            <div class="step-container">
                <div class="step-item step-1">
                    <div>{folder_icon}</div>
                    <div class="step-title" style="color:#A0C4FF;">Step 1</div>
                    <div class="step-desc">여기에 1단계 설명을 적으세요.</div>
                </div>
                <div class="step-item step-2">
                    <div>{bear_icon}</div>
                    <div class="step-title" style="color:#FFD580;">Step 2</div>
                    <div class="step-desc">여기에 2단계 설명을 적으세요.</div>
                </div>
                <div class="step-item step-3">
                    <div>{book_icon}</div>
                    <div class="step-title" style="color:#FF9EAA;">Step 3</div>
                    <div class="step-desc">여기에 3단계 설명을 적으세요.</div>
                </div>
            </div>
        """), unsafe_allow_html=True)

    with right_col:
        # [디자인 적용] 우측 액션 카드 (입력 폼)
        st.markdown(styles.Utils.clean_html("""
            <div class="landing-action">
                <div class="action-header">
                    👇 여기에 기능을 배치하세요
                </div>
            </div>
        """), unsafe_allow_html=True)
        
        # 사용자님의 기존 입력 위젯 (파일 업로더 등)
        # CSS가 자동으로 적용되어 예쁜 디자인으로 표시됩니다.
        uploaded_file = st.file_uploader("파일 업로드", label_visibility="collapsed")
        
        if st.button("실행하기"):
            st.info("버튼이 클릭되었습니다! (기존 로직 실행)")

if __name__ == "__main__":
    main()