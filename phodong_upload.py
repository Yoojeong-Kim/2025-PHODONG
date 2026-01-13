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

# ==============================================================================
# [로직] AI 서비스 클래스 (Gemini & TTS)
# ==============================================================================

class PhodongService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            st.error("GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
            return
        
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
            with st.spinner("🧸 포동이가 사진 속 친구를 살펴보고 있어요..."):
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
            st.error("캐릭터를 분석하는 중 오류가 발생했어요.")
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
            with st.spinner("📖 포동이가 이야기를 짓고 있어요..."):
                response = self.model.generate_content(prompt)
                cleaned_text = Utils.clean_json_text(response.text)
                data = json.loads(cleaned_text)
                
                # 기존 카드에 내용 업데이트
                card.story_narration = data.get("story_narration", "")
                card.dialogue = data.get("dialogue", "")
                return card
        except Exception as e:
            logger.error(f"스토리 생성 실패: {e}")
            st.error("이야기를 만드는 중 오류가 발생했어요.")
            return None

    def text_to_speech(self, text: str) -> Optional[io.BytesIO]:
        """gTTS를 사용해 텍스트를 음성으로 변환"""
        try:
            tts = gTTS(text=text, lang='ko')
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            return mp3_fp
        except Exception as e:
            logger.error(f"TTS 생성 실패: {e}")
            return None

# ==============================================================================
# [UI] 메인 화면
# ==============================================================================

def main():
    # 스타일 적용 (styles.py에 apply_custom_css 함수가 있다고 가정)
    if hasattr(styles, 'apply_custom_css'):
        styles.apply_custom_css()
    else:
        st.markdown("<style>.stApp { background-color: #f9f9f9; }</style>", unsafe_allow_html=True)

    st.title("📸 포동 PHODONG - 나만의 포토 스토리북")
    st.markdown("##### 우리 집 물건들이 들려주는 신비한 이야기")

    # 서비스 인스턴스 초기화
    service = PhodongService()

    # 사이드바: 사용자 설정
    with st.sidebar:
        st.header("⚙️ 이야기 설정")
        child_name = st.text_input("아이 이름 (닉네임)", value="포동이")
        age = st.slider("아이 연령", 3, 9, 5)
        partner_name = st.text_input("함께하는 어른", value="엄마")
        
        st.markdown("---")
        selected_genre = st.selectbox("이야기 장르", GENRE_OPTIONS)
        selected_purpose = st.selectbox("교육 목표", PURPOSE_OPTIONS)
        
        config = StoryConfig(
            child_name=child_name,
            partner_name=partner_name,
            age=age,
            genre=selected_genre,
            purpose=selected_purpose
        )

    # 메인 영역: 이미지 업로드
    uploaded_file = st.file_uploader("이야기의 주인공이 될 사진을 올려주세요! (장난감, 인형, 컵 등)", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        
        # 레이아웃 분할
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.image(image, caption="업로드된 사진", use_container_width=True)
            process_btn = st.button("✨ 이야기 만들기 시작!", use_container_width=True, type="primary")

        # 버튼 클릭 시 로직 수행
        if process_btn:
            with col2:
                # 1. 이미지 분석 & 캐릭터 생성
                story_card = service.analyze_image_and_create_character(image, config)
                
                if story_card:
                    st.success(f"짜잔! **{story_card.character_name}** 친구를 발견했어요!")
                    
                    # 캐릭터 카드 시각화 (간단한 정보 표시)
                    with st.expander("🔍 캐릭터 정보 보기", expanded=True):
                        st.markdown(f"""
                        - **이름:** {story_card.character_name}
                        - **종류:** {story_card.character_type}
                        - **성격:** {story_card.personality}
                        - **능력:** {story_card.magic_power}
                        """)

                    # 2. 스토리 생성
                    final_card = service.generate_story_segment(story_card, config)
                    
                    if final_card:
                        st.markdown("### 📖 오늘의 이야기")
                        st.info(final_card.story_narration)
                        
                        st.markdown(f"**💬 {final_card.character_name}의 말:**")
                        st.write(f"\"{final_card.dialogue}\"")
                        
                        # 3. 오디오 생성 (대사 부분)
                        audio_fp = service.text_to_speech(final_card.dialogue)
                        if audio_fp:
                            st.audio(audio_fp, format='audio/mp3')

if __name__ == "__main__":
    main()