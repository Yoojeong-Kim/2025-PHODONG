import streamlit as st
import time
import io
import styles  # styles.py 임포트 (디자인 엔진)

# ==============================================================================
# [필수 1] 페이지 기본 설정
# ==============================================================================
st.set_page_config(
    page_title="포동 PHODONG - Live",
    page_icon="🧸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

class CameraManager:
    """카메라 촬영 및 캡처된 이미지 관리를 담당하는 클래스"""
    
    @staticmethod
    def init_state():
        if "camera_captures" not in st.session_state:
            st.session_state.camera_captures = []

    @staticmethod
    def render_camera_ui():
        """카메라 UI를 렌더링하고 로직을 처리합니다."""
        CameraManager.init_state()

        # [디자인 적용] 페이지 타이틀
        st.markdown(styles.Utils.clean_html("""
            <h2 class="font-heading" style="color:#3A3A3A;">📸 실시간 촬영 모드</h2>
            <p>카메라 버튼을 누르면 사진이 오른쪽에 모여요. (웹 환경에서는 수동 촬영만 가능합니다)</p>
        """), unsafe_allow_html=True)

        c1, c2 = st.columns([1, 1], gap="large")
        
        # === [왼쪽] 카메라 입력창 ===
        with c1:
            st.markdown('<div class="content-box">', unsafe_allow_html=True)
            st.markdown('<div class="font-heading" style="color:#FF9EAA; margin-bottom:15px;">🎥 찰칵!</div>', unsafe_allow_html=True)
            
            cam_image = st.camera_input("카메라", label_visibility="collapsed")
            
            if cam_image:
                bytes_data = cam_image.getvalue()
                # 중복 방지 (가장 최근 사진과 비교)
                if not st.session_state.camera_captures or st.session_state.camera_captures[-1] != bytes_data:
                    st.session_state.camera_captures.append(bytes_data)
                    st.toast(f"📸 찰칵! ({len(st.session_state.camera_captures)}장 저장됨)")
                    time.sleep(0.5) 
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # === [오른쪽] 찍은 사진 갤러리 & 완료 버튼 ===
        with c2:
            st.markdown('<div class="content-box" style="background:#FFF0F5; border-color:#FF9EAA;">', unsafe_allow_html=True)
            
            # 헤더 영역
            st.markdown(f"""
                <div class="font-heading" style="color:#555; margin-bottom:15px;">
                    🖼️ 모은 조각들 <span style="font-size:0.9rem; color:#888;">({len(st.session_state.camera_captures)}장)</span>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.camera_captures:
                # 갤러리 뷰 (3열 그리드)
                cols = st.columns(3)
                for idx, img_bytes in enumerate(st.session_state.camera_captures):
                    with cols[idx % 3]:
                        st.image(img_bytes, use_container_width=True)
                
                st.markdown("<hr style='border:1px dashed #FF9EAA; opacity:0.3; margin:20px 0;'>", unsafe_allow_html=True)
                
                # 액션 버튼들
                col_act1, col_act2 = st.columns(2)
                with col_act1:
                    if st.button("🗑️ 비우기"):
                        st.session_state.camera_captures = []
                        st.rerun()
                with col_act2:
                    if st.button("✨ 이야기 만들기"):
                        return [io.BytesIO(b) for b in st.session_state.camera_captures]
            else:
                # [디자인 적용] 사진 없을 때 아이콘 표시
                st.markdown(f"""
                    <div style="text-align:center; padding:30px;">
                        {styles.ArtWork.get_camera_lens(80)}
                        <p style="margin-top:20px; color:#888; font-family:'Jua';">
                            아직 찍은 사진이 없어요.<br>
                            왼쪽에서 찰칵! 찍어보세요.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        return None

def main():
    # 1. 스타일 주입 (필수)
    styles.DesignSystem.inject_css()

    # 2. 헤더 섹션
    bear = styles.ArtWork.get_bear(45)
    c1, c2 = st.columns([0.8, 11.2])
    with c1: st.markdown(f"<div>{bear}</div>", unsafe_allow_html=True)
    with c2: 
        st.markdown(styles.Utils.clean_html("""
            <div style="display:flex; align-items:center; height:100%;">
                <h3 class='font-heading' style='color:#FF9EAA; margin:0; font-size:1.8rem;'>포동 LIVE</h3>
            </div>
        """), unsafe_allow_html=True)
    st.markdown("<hr style='margin: 15px 0 40px 0; border:0; border-top:2px solid #F0F0F0;'>", unsafe_allow_html=True)

    # 3. 카메라 로직 실행
    result_images = CameraManager.render_camera_ui()
    
    # 4. 결과 처리 (이야기 만들기 버튼 클릭 시)
    if result_images:
        st.success("사진 촬영이 완료되었습니다! 다음 단계로 넘어갑니다.")
        # 여기에 다음 페이지로 넘어가는 로직 등을 추가하시면 됩니다.

if __name__ == "__main__":
    main()