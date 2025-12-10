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
        st.info("카메라 버튼을 누르면 사진이 아래에 모여요. (웹 환경에서는 수동 촬영만 가능합니다)")

        c1, c2 = st.columns([1, 1], gap="medium")
        
        # [왼쪽] 카메라 입력창
        with c1:
            cam_image = st.camera_input("찰칵!", label_visibility="collapsed")
            
            if cam_image:
                bytes_data = cam_image.getvalue()
                # 중복 방지 (가장 최근 사진과 비교)
                if not st.session_state.camera_captures or st.session_state.camera_captures[-1] != bytes_data:
                    st.session_state.camera_captures.append(bytes_data)
                    st.toast(f"📸 찰칵! ({len(st.session_state.camera_captures)}장 저장됨)")
                    time.sleep(0.5) 
                    st.rerun()

        # [오른쪽] 찍은 사진 갤러리 & 완료 버튼
        with c2:
            st.markdown(f"**🖼️ 모은 조각들 ({len(st.session_state.camera_captures)}장)**")
            
            if st.session_state.camera_captures:
                # 갤러리 뷰 (3열 그리드)
                cols = st.columns(3)
                for idx, img_bytes in enumerate(st.session_state.camera_captures):
                    with cols[idx % 3]:
                        # 이미지는 꽉 차게 보여주는 것이 좋으므로 use_container_width 사용
                        st.image(img_bytes, use_container_width=True)
                
                st.markdown("---")
                
                col_act1, col_act2 = st.columns(2)
                with col_act1:
                    # 버튼의 width 옵션 제거 (CSS가 처리함)
                    if st.button("🗑️ 비우기"):
                        st.session_state.camera_captures = []
                        st.rerun()
                with col_act2:
                    # 버튼의 width 옵션 제거 (CSS가 처리함)
                    if st.button("✨ 이야기 만들기", type="primary"):
                        return [io.BytesIO(b) for b in st.session_state.camera_captures]
            else:
                st.markdown("""
                <div style="padding:20px; border:2px dashed #DDD; border-radius:10px; text-align:center; color:#AAA;">
                    아직 찍은 사진이 없어요.<br>왼쪽에서 찰칵! 찍어보세요.
                </div>
                """, unsafe_allow_html=True)
        
        return None