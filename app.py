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

# styles.py 임포트 (디자인 시스템)
import styles

# ==============================================================================
# 1. ⚙️ CORE CONFIGURATION & CONSTANTS
# ==============================================================================
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="포동 PHODONG",
    page_icon="🧸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("PhodongApp")

# 상수 정의
DEFAULT_MODEL = "gemini-pro"
GENRE_OPTIONS = ["전래동화", "판타지", "히어로", "요정", "일상", "자동차", "공주/왕자", "추리", "우주", "로봇", "동물", "공룡"]
PURPOSE_OPTIONS = ["안전 교육", "예절&규칙", "생활 습관", "어휘력 향상", "세계&다양성", "창의력/사고력", "기초과학", "자존감 높이기"]

# ==============================================================================
# 2. 📦 DATA STRUCTURES
# ==============================================================================
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
# 3. 🧠 AI SERVICE LAYER
# ==============================================================================
class Utils:
    @staticmethod
    def clean_json_text(text):
        """Gemini 응답 정리"""
        text = text.strip()
        if text.startswith("```json"): text = text[7:]
        elif text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        return text.strip()

class PhodongService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            st.error("🚨 API Key가 없습니다. .env 파일을 확인해주세요.")
            st.stop()
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(DEFAULT_MODEL)

    def analyze_image_and_create_character(self, image: Image.Image, config: StoryConfig) -> Optional[StoryCard]:
        """[1단계] 이미지 분석 및 캐릭터 생성"""
        prompt = f"""
        당신은 {config.age}세 어린이를 위한 '{config.genre}' 장르의 전문 동화 작가입니다.
        업로드된 이미지를 분석하여 동화의 주인공 캐릭터를 설정해주세요.

        [분석 설정]
        - 장르: {config.genre} (이 분위기에 맞는 캐릭터로 해석하세요)
        - 교육 목표: {config.purpose} (이 목표를 달성할 수 있는 성격을 부여하세요)
        
        [출력 포맷 (JSON)]
        {{
            "character_name": "아이들이 좋아할 귀여운 한국어 이름",
            "character_type": "사물/동물의 종류 (예: 용감한 소방차, 마법 곰인형)",
            "personality": "성격 (교육 목표와 관련된 긍정적 성격 1문장)",
            "magic_power": "동화적 상상력이 담긴 특수 능력 (1문장)"
        }}
        """
        try:
            response = self.model.generate_content([prompt, image])
            data = json.loads(Utils.clean_json_text(response.text))
            return StoryCard(
                character_name=data.get("character_name", "알 수 없음"),
                character_type=data.get("character_type", "-"),
                personality=data.get("personality", "-"),
                magic_power=data.get("magic_power", "-")
            )
        except Exception as e:
            logger.error(f"Character Gen Error: {e}")
            return None

    def generate_story_segment(self, card: StoryCard, config: StoryConfig) -> Optional[StoryCard]:
        """[2단계] 동화 내용 생성"""
        prompt = f"""
        당신은 베스트셀러 동화 작가입니다. 아래 설정에 맞춰 짧은 동화의 한 장면을 작성하세요.

        [핵심 설정]
        - 독자: {config.child_name} ({config.age}세)
        - 함께 읽는 사람: {config.partner_name}
        - 장르: {config.genre}
        - ★교육 목표: {config.purpose} (이야기를 통해 아이가 이 가치를 배우게 하세요)

        [캐릭터]
        - 이름: {card.character_name} ({card.character_type})
        - 성격: {card.personality}

        [작성 요구사항]
        1. 말투: {config.age}세 아이가 이해하기 쉬운 다정하고 생동감 넘치는 '해요체'.
        2. 내용: 교육 목표가 자연스럽게 녹아든 흥미진진한 도입부.
        3. story_narration: 상황을 묘사하는 지문 (3~4문장).
        4. dialogue: 캐릭터가 아이({config.child_name})에게 직접 말을 거는 대사 (1~2문장).

        [출력 포맷 (JSON)]
        {{
            "story_narration": "동화 지문 내용...",
            "dialogue": "캐릭터 대사..."
        }}
        """
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(Utils.clean_json_text(response.text))
            card.story_narration = data.get("story_narration", "")
            card.dialogue = data.get("dialogue", "")
            return card
        except Exception as e:
            logger.error(f"Story Gen Error: {e}")
            return None

    def text_to_speech(self, text: str) -> Optional[io.BytesIO]:
        """[3단계] TTS 생성"""
        try:
            if not text: return None
            tts = gTTS(text=text, lang='ko')
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            return mp3_fp
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            return None

# ==============================================================================
# 4. 🖥️ UI / VIEW LAYER
# ==============================================================================

def main():
    # 스타일 적용
    if hasattr(styles, 'apply_custom_css'):
        styles.apply_custom_css()
    else:
        styles.DesignSystem.inject_css()

    # ▼▼▼ [여기서부터 진단 코드입니다] ▼▼▼
    import google.generativeai as genai
    import streamlit as st
    import os

    st.title("🛠️ 긴급 모델 점검")
    
    # 1. API 키 확인
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("❌ API 키가 없습니다! .env 파일이나 Secrets 설정을 확인하세요.")
        st.stop()
    else:
        st.success(f"✅ API 키 확인됨 (시작: {api_key[:4]}***)")

    # 2. 라이브러리 버전 확인
    st.info(f"📦 설치된 SDK 버전: {genai.__version__}")

    # 3. 사용 가능한 모델 리스트 출력 (가장 중요!)
    try:
        genai.configure(api_key=api_key)
        models = []
        for m in genai.list_models():
            # 'generateContent' 메서드를 지원하는 모델만 필터링
            if 'generateContent' in m.supported_generation_methods:
                models.append(m.name)
        
        st.write("🔑 **내 API 키로 쓸 수 있는 모델 목록:**")
        st.json(models) # 여기에 뜨는 이름 중 하나를 골라야 합니다!

    except Exception as e:
        st.error(f"❌ 모델 목록 조회 실패! API 키가 잘못되었거나 권한이 없습니다.\n에러 내용: {e}")
    # ▲▲▲ [진단 코드 끝] ▲▲▲

'''
def main():
    # 0. 초기화
    styles.DesignSystem.inject_css() # CSS 주입
    service = PhodongService()

    # 1. 헤더 (레퍼런스 스타일)
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

    # 2. 메인 레이아웃 (2컬럼)
    left_col, right_col = st.columns([1.3, 1], gap="large")

    # --- [왼쪽] 소개 및 가이드 ---
    with left_col:
        st.markdown("""
            <div class="landing-hero">
                <h1 class="landing-title">포동 PHODONG</h1>
                <p class="landing-subtitle">
                    아이의 소중한 순간들이<br>
                    세상에 하나뿐인 <b>동화책</b>이 됩니다.
                </p>
            </div>
        """, unsafe_allow_html=True)

        folder_icon = styles.ArtWork.get_folder(40)
        bear_icon = styles.ArtWork.get_bear(40)
        book_icon = styles.ArtWork.get_book_cover(40)

        st.markdown(styles.Utils.clean_html(f"""
            <div class="step-container">
                <div class="step-item step-1">
                    <div>{folder_icon}</div>
                    <div class="step-title" style="color:#A0C4FF;">1. 정보 입력</div>
                    <div class="step-desc">아이의 이름과 좋아하는 장르를 알려주세요.</div>
                </div>
                <div class="step-item step-2">
                    <div>{bear_icon}</div>
                    <div class="step-title" style="color:#FFD580;">2. 사진 찰칵</div>
                    <div class="step-desc">장난감이나 물건 사진을 올려주세요.</div>
                </div>
                <div class="step-item step-3">
                    <div>{book_icon}</div>
                    <div class="step-title" style="color:#FF9EAA;">3. 이야기 완성</div>
                    <div class="step-desc">AI가 들려주는 마법 같은 이야기를 만나요.</div>
                </div>
            </div>
        """), unsafe_allow_html=True)

    # --- [오른쪽] 입력 폼 (정보 입력 -> 사진 업로드 -> 버튼) ---
    with right_col:
        st.markdown(styles.Utils.clean_html("""
            <div class="landing-action">
                <div class="action-header">
                    👇 여기서 이야기를 시작해요!
                </div>
        """), unsafe_allow_html=True)

        # [입력 1] 기본 정보 (HTML div 밖에서 Streamlit 위젯 사용)
        col_input1, col_input2 = st.columns(2)
        with col_input1:
            child_name = st.text_input("아이 이름", value="포동이")
        with col_input2:
            age = st.slider("아이 연령", 3, 9, 5)
        
        partner_name = st.text_input("함께하는 어른 (호칭)", value="엄마")
        
        col_select1, col_select2 = st.columns(2)
        with col_select1:
            genre = st.selectbox("이야기 장르", GENRE_OPTIONS)
        with col_select2:
            purpose = st.selectbox("교육 목표", PURPOSE_OPTIONS)

        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        # [입력 2] 파일 업로드
        uploaded_file = st.file_uploader("주인공 사진 업로드", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
        
        # [실행] 버튼
        process_btn = st.button("✨ 이야기 만들기 시작!", type="primary", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True) # landing-action 닫기

        # --- 로직 실행 ---
        if process_btn:
            if uploaded_file:
                # 설정 객체 생성
                config = StoryConfig(child_name, partner_name, age, genre, purpose)
                image = Image.open(uploaded_file)
                
                # 작은 미리보기
                st.image(image, caption="선택한 사진", width=150)

                with st.spinner("🧸 포동이가 사진을 보며 이야기를 만들고 있어요..."):
                    # 1. 이미지 분석
                    story_card = service.analyze_image_and_create_character(image, config)
                    
                    if story_card:
                        # 2. 스토리 생성
                        final_card = service.generate_story_segment(story_card, config)
                        
                        if final_card:
                            # 3. 오디오 생성
                            audio_fp = service.text_to_speech(final_card.dialogue)
                            
                            # --- 결과 표시 (확장 패널 자동 열림) ---
                            st.divider()
                            with st.expander("✨ 완성된 이야기 열기", expanded=True):
                                st.success(f"**{final_card.character_name}** 친구가 찾아왔어요!")
                                
                                # 결과 레이아웃
                                r_c1, r_c2 = st.columns([1, 2])
                                with r_c1:
                                    st.markdown(f"""
                                    <div class='profile-group'>
                                        <span class='badge-pill badge-pink'>{final_card.character_name}</span><br>
                                        <span class='badge-pill badge-yellow'>{final_card.personality}</span>
                                        <div style='margin-top:10px; font-size:0.9rem; color:#666;'>
                                            <b>종류:</b> {final_card.character_type}<br>
                                            <b>능력:</b> {final_card.magic_power}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.image(image, use_container_width=True)
                                
                                with r_c2:
                                    st.markdown(f"""
                                    <div class='dialogue-box'>
                                        <div class='dialogue-text'>"{final_card.dialogue}"</div>
                                    </div>
                                    <div class='context-box'>
                                        {final_card.story_narration}
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    if audio_fp:
                                        st.audio(audio_fp, format='audio/mp3')
                        else:
                            st.error("이야기를 만드는 데 실패했어요.")
                    else:
                        st.error("캐릭터를 분석하지 못했어요.")
            else:
                st.warning("사진을 먼저 올려주세요!")
'''

if __name__ == "__main__":
    main()
