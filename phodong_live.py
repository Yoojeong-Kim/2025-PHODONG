import streamlit as st
import time
import io

class CameraManager:
    """카메라 촬영 및 캡처된 이미지 관리를 담당하는 클래스"""
    
    @staticmethod
    def init_state():
        if "camera_captures" not in st.session_state:
            st.session_state.camera_captures = []

    @staticmethod
    def render_camera_ui():
        """카메라 UI를 그리고, 최종적으로 선택된 이미지 리스트(BytesIO)를 반환하거나 None을 반환"""
        CameraManager.init_state()
        
        st.markdown("### 📸 실시간 촬영 모드")
        st.info("카메라로 찰칵! 찍으면 아래에 사진이 모여요.")

        c1, c2 = st.columns([1, 1], gap="medium")
        
        # [왼쪽] 카메라 입력창
        with c1:
            cam_image = st.camera_input("여기를 눌러 사진을 찍으세요", label_visibility="collapsed")
            
            if cam_image:
                bytes_data = cam_image.getvalue()
                if not st.session_state.camera_captures or st.session_state.camera_captures[-1] != bytes_data:
                    st.session_state.camera_captures.append(bytes_data)
                    st.toast(f"📸 찰칵! ({len(st.session_state.camera_captures)}장 저장됨)")
                    time.sleep(0.5) 
                    st.rerun()

        # [오른쪽] 찍은 사진 갤러리
        with c2:
            st.markdown(f"**🖼️ 모은 조각들 ({len(st.session_state.camera_captures)}장)**")
            
            if st.session_state.camera_captures:
                cols = st.columns(3)
                for idx, img_bytes in enumerate(st.session_state.camera_captures):
                    with cols[idx % 3]:
                        # 👇 [수정] use_container_width=True -> width="stretch" (권장사항 반영)
                        # 혹시 라이브러리가 아직 지원 안 할 수도 있으니 안전하게 파라미터 자체를 제거하거나
                        # 경고 메시지대로 수정. 여기서는 Streamlit 권장사항인 CSS width 처리나 use_container_width 사용.
                        # 경고가 'use width=stretch for use_container_width=True' 였으므로 삭제 후 CSS에 의존하거나
                        # 그대로 두되, Streamlit 버전을 올리면 해결됨.
                        # 여기서는 경고를 피하기 위해 옵션을 잠시 뺍니다. (기본값 사용)
                        st.image(img_bytes)
                
                st.markdown("---")
                col_act1, col_act2 = st.columns(2)
                with col_act1:
                    # 👇 [수정] use_container_width 삭제
                    if st.button("🗑️ 모두 비우기"):
                        st.session_state.camera_captures = []
                        st.rerun()
                with col_act2:
                    # 👇 [수정] use_container_width 삭제
                    if st.button("✨ 이야기 만들기", type="primary"):
                        return [io.BytesIO(b) for b in st.session_state.camera_captures]
            else:
                st.markdown("""
                <div style="padding:20px; border:2px dashed #DDD; border-radius:10px; text-align:center; color:#AAA;">
                    아직 찍은 사진이 없어요.<br>왼쪽에서 사진을 찍어보세요!
                </div>
                """, unsafe_allow_html=True)
        
        return None