import streamlit as st
import os
import json
import io
import logging
from dataclasses import dataclass
from typing import Optional
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS

import styles  # styles.py에 정의된 디자인/아이콘 모듈 임포트

# ==============================================================================
# [초기 설정] 환경변수, 로깅, 상수 정의 (Source B에서 가져옴)
# ==============================================================================
# .env 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("PhodongCore")

# 상수 정의
DEFAULT_MODEL = "gemini-1.5-flash" # 또는 gemini-pro-vision 등 사용 가능한 모델
GENRE_OPTIONS = ["전래동화", "판타지", "히어로", "요정", "일상", "자동차", "공주/왕자", "추리", "우주", "로봇", "동물", "공룡"]
PURPOSE_OPTIONS = ["안전", "예절&규칙", "문화", "어휘력", "세계&다양성", "사고력", "기초과학", "자신감"]

# 데이터 클래스 정의
@dataclass
class StoryConfig:
    child_name: str = ""
    partner_name: str = ""
    age: int = 5
    genre: str = GENRE_OPTIONS[0]
    purpose: str = PURPOSE_OPTIONS[0]

@dataclass
class StoryCard:
    character_name: str = "알 수 없음"
    character_type: str = "-"
    personality: str = "-"
    magic_power: str = "-"
    story_narration: str = ""
    dialogue: str = ""
    image_key: Optional[str] = None

# ==============================================================================
# [로직] 유틸리티 및 AI 서비스 클래스 (Source B에서 완성된 코드 가져옴)
# ==============================================================================
class Utils:
    @staticmethod
    def clean_json_text(text):
        """Gemini 응답에서 마크다운 코드 블록 제거 및 JSON 파싱 준비"""
        text = text.strip()
        # 마크다운 코드 블록 제거 (```json ... ```)
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        return text.strip()

class PhodongService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            st.error("GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
            st.stop() # 키가 없으면 더 이상 진행하지 않음
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(DEFAULT_MODEL)

    def analyze_image_and_create_character(self, image: Image.Image, config: StoryConfig) -> Optional[StoryCard]:
        """이미지를 분석하여 캐릭터 정보를 JSON으로 추출"""
        prompt = f"""
        당신은 아이들을 위한 동화 작가이자 캐릭터 디자이너입니다.
        제공된 이미지를 분석하여 다음 정보를 JSON 형식으로 추출해주세요.
        
        [설정]
        - 대상 연령: {config.age}세
        - 장르: {config.genre}
        - 목적: {config.purpose}
        
        [출력 포맷 (JSON)]
        {{
            "character_name": "캐릭터에게 어울리는 귀여운 한국어 이름",
            "character_type": "사물/동물의 종류 (예: 곰인형, 자동차, 컵)",
            "personality": "성격 (한 문장)",
            "magic_power": "이 캐릭터가 가진 작고 귀여운 마법 능력 (한 문장)"
        }}
        
        반드시 순수 JSON만 출력하세요.
        """
        
        try:
            # spinner는 호출하는 쪽에서 제어하도록 제거
            response = self.model.generate_content([prompt, image])
            cleaned_text = Utils.clean_json_text(response.text)
            data = json.loads(cleaned_text)
            
            return StoryCard(
                character_name=data.get("character_name", "알 수 없음"),
                character_type=data.get("character_type", "-"),
                personality=data.get("personality", "-"),
                magic_power=data.get("magic_power", "-")
            )
        except Exception as e:
            logger.error(f"이미지 분석 실패: {e}")
            # st.error는 호출하는 쪽에서 처리
            return None

    def generate_story_segment(self, card: StoryCard, config: StoryConfig) -> Optional[StoryCard]:
        """캐릭터 정보를 바탕으로 짧은 동화와 대사 생성"""
        prompt = f"""
        다음 캐릭터를 주인공으로 한 짧은 동화의 도입부를 작성해주세요.
        
        [캐릭터 정보]
        - 이름: {card.character_name}
        - 종류: {card.character_type}
        - 성격: {card.personality}
        - 능력: {card.magic_power}
        
        [동화 설정]
        - 독자: {config.child_name} ({config.age}세 어린이)
        - 파트너: {config.partner_name} (부모님/선생님 등)
        - 장르: {config.genre}
        - 교육 목표: {config.purpose}
        
        [요청 사항]
        1. {config.age}세 아이가 이해하기 쉬운 따뜻한 어조로 작성하세요.
        2. 'story_narration'은 상황을 설명하는 지문입니다. (3~4문장)
        3. 'dialogue'는 캐릭터가 아이에게 말을 거는 대사입니다. (1~2문장)
        
        [출력 포맷 (JSON)]
        {{
            "story_narration": "동화 내용...",
            "dialogue": "캐릭터의 대사..."
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            cleaned_text = Utils.clean_json_text(response.text)
            data = json.loads(cleaned_text)
            
            # 기존 카드에 내용 업데이트
            card.story_narration = data.get("story_narration", "")
            card.dialogue = data.get("dialogue", "")
            return card
        except Exception as e:
            logger.error(f"스토리 생성 실패: {e}")
            return None

    def text_to_speech(self, text: str) -> Optional[io.BytesIO]:
        """gTTS를 사용해 텍스트를 음성으로 변환"""
        try:
            if not text: return None
            tts = gTTS(text=text, lang='ko')
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            return mp3_fp
        except Exception as e:
            logger.error(f"TTS 생성 실패: {e}")
            return None

# ==============================================================================
# [필수 1] 페이지 기본 설정 (Source A)
# ==============================================================================
st.set_page_config(
    page_title="포동 PHODONG",
    page_icon="🧸",
    layout="wide",
    initial_sidebar_state="collapsed" # 사이드바 기본은 닫힘 상태
)

# ==============================================================================
# [메인 UI 및 실행 로직] (Source A 디자인 + Source B 로직 통합)
# ==============================================================================
def main():
    # 0. 서비스 인스턴스 초기화
    service = PhodongService()

    # 1. 스타일 주입
    styles.DesignSystem.inject_css()

    # --------------------------------------------------------------------------
    # [사이드바] 설정 영역 (Source B에서 가져옴)
    # --------------------------------------------------------------------------
    with st.sidebar:
        st.header("⚙️ 이야기 설정")
        st.caption("아이에게 맞는 이야기를 위해 설정해주세요.")
        child_name = st.text_input("아이 이름 (닉네임)", value="포동이")
        age = st.slider("아이 연령", 3, 9, 5)
        partner_name = st.text_input("함께하는 어른", value="엄마")
        
        st.markdown("---")
        selected_genre = st.selectbox("이야기 장르", GENRE_OPTIONS)
        selected_purpose = st.selectbox("교육 목표", PURPOSE_OPTIONS)
        
        # 설정 객체 생성
        config = StoryConfig(
            child_name=child_name,
            partner_name=partner_name,
            age=age,
            genre=selected_genre,
            purpose=selected_purpose
        )

    # --------------------------------------------------------------------------
    # [메인 콘텐츠] 헤더 및 랜딩 페이지 디자인 (Source A)
    # --------------------------------------------------------------------------
    # 헤더 섹션
    bear = styles.ArtWork.get_bear(45)
    c1, c2 = st.columns([0.8, 11.2])
    with c1: st.markdown(f"<div>{bear}</div>", unsafe_allow_html=True)
    with c2: 
        st.markdown(styles.Utils.clean_html("""
            <div style="display:flex; align-items:center; height:100%;">
                <h3 class='font-heading' style='color:#FF9EAA; margin:0; font-size:1.8rem;'>mobile prototype</h3>
            </div>
        """), unsafe_allow_html=True)
    st.markdown("<hr style='margin: 15px 0 40px 0; border:0; border-top:2px solid #F0F0F0;'>", unsafe_allow_html=True)

    # 메인 2단 레이아웃
    left_col, right_col = st.columns([1.3, 1], gap="large")

    with left_col:
        # 좌측: 제목 및 3단계 가이드 (디자인 유지)
        st.markdown("""
            <h1 class="landing-title">포동 PHODONG</h1>
            <p class="landing-subtitle">아이의 소중한 순간들이 세상에 하나뿐인 동화책이 됩니다.</p>
        """, unsafe_allow_html=True)
        
        folder_icon = styles.ArtWork.get_folder(40)
        bear_icon = styles.ArtWork.get_bear(40)
        book_icon = styles.ArtWork.get_book_cover(40)
        
        st.markdown(styles.Utils.clean_html(f"""
            <div class="step-container">
                <div class="step-item step-1">
                    <div>{folder_icon}</div>
                    <div class="step-title" style="color:#A0C4FF;">조각 모으기</div>
                    <div class="step-desc">이야기를 만들기 위한 사진조각을 준비해요.</div>
                </div>
                <div class="step-item step-2">
                    <div>{bear_icon}</div>
                    <div class="step-title" style="color:#FFD580;">마법부리기</div>
                    <div class="step-desc">포동이가 재미있는 이야기를 만들어요.</div>
                </div>
                <div class="step-item step-3">
                    <div>{book_icon}</div>
                    <div class="step-title" style="color:#FF9EAA;">동화책 완성</div>
                    <div class="step-desc">예쁜 표지와 목소리를 선물받아요.</div>
                </div>
            </div>
        """), unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # [우측 액션 카드 & 로직 연결] (핵심 통합 부분)
    # --------------------------------------------------------------------------
    result_card = None # 결과 저장을 위한 변수
    audio_file = None

    with right_col:
        st.markdown(styles.Utils.clean_html("""
            <div class="landing-action">
                <div class="action-header">
                    👇 여기로 이야기 조각을 보내주세요!
                </div>
            </div>
        """), unsafe_allow_html=True)
        
        # 파일 업로더
        uploaded_file = st.file_uploader("파일 업로드", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
        
        # 실행 버튼 (type="primary"로 강조)
        process_btn = st.button("✨ 이야기 만들기 시작!", type="primary", use_container_width=True)

        # [로직 실행 조건] 버튼 클릭 AND 파일 업로드됨
        if process_btn and uploaded_file:
            image = Image.open(uploaded_file)
            # 우측 카드에 업로드된 이미지 작게 보여주기
            st.image(image, caption="선택한 사진", use_container_width=True)

            # 전체 진행 과정을 스피너로 감쌈
            with st.spinner("🧸 포동이가 사진을 보며 이야기를 만들고 있어요... (잠시만 기다려주세요!)"):
                # 1. 이미지 분석
                story_card = service.analyze_image_and_create_character(image, config)
                
                if story_card:
                    # 2. 스토리 생성
                    final_card = service.generate_story_segment(story_card, config)
                    
                    if final_card:
                        # 3. TTS 생성
                        audio_fp = service.text_to_speech(final_card.dialogue)
                        
                        # 결과 저장을 위해 변수에 할당
                        result_card = final_card
                        audio_file = audio_fp
                    else:
                        st.error("이야기를 생성하는 데 실패했어요. 다시 시도해주세요.")
                else:
                    st.error("캐릭터를 분석하는 데 실패했어요. 사진을 확인해주세요.")
                    
        elif process_btn and not uploaded_file:
            st.warning("먼저 사진 조각(이미지 파일)을 올려주세요!")

    # --------------------------------------------------------------------------
    # [결과 표시 영역] 메인 레이아웃 하단에 넓게 표시
    # --------------------------------------------------------------------------
    if result_card:
        st.divider() # 구분선
        # 결과를 보여주는 확장 패널 (자동으로 열림)
        with st.expander("✨ 완성된 이야기 열기", expanded=True):
            st.success(f"짜잔! **{result_card.character_name}** 친구가 찾아왔어요!")
            
            col_res1, col_res2 = st.columns([1, 2])
            
            with col_res1:
                # 캐릭터 정보 및 원본 이미지
                st.markdown(f"""
                ### 🔍 캐릭터 정보
                - **이름:** {result_card.character_name}
                - **종류:** {result_card.character_type}
                - **성격:** {result_card.personality}
                - **능력:** {result_card.magic_power}
                """)
                if uploaded_file:
                     st.image(uploaded_file, caption=f"{result_card.character_name}의 모습", use_container_width=True)

            with col_res2:
                # 스토리 및 오디오
                st.markdown("### 📖 오늘의 이야기 도입부")
                
                # 지문 박스 디자인 적용 (styles.py 활용 예시 - 필요시 수정)
                st.markdown(f"""
                <div style="background-color:#fdf6f0; padding:20px; border-radius:15px; margin-bottom:20px;">
                    {result_card.story_narration}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"**💬 {result_card.character_name}의 목소리:**")
                st.write(f"\"{result_card.dialogue}\"")
                
                if audio_file:
                    st.audio(audio_file, format='audio/mp3')

if __name__ == "__main__":
    main()