import streamlit as st
import os
import json
import io
import logging
import base64
from dataclasses import dataclass
from typing import Optional, List
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS

# styles.py 임포트 (디자인 시스템)
import styles

# ==============================================================================
# 1. ⚙️ 설정 및 상태 관리
# ==============================================================================
load_dotenv()

st.set_page_config(
    page_title="포동 PHODONG",
    page_icon="🧸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("PhodongApp")

# [모델 설정]
TEXT_MODEL_NAME = "gemini-2.5-flash"
IMAGE_MODEL_NAME = "gemini-2.0-flash-exp-image-generation"

GENRE_OPTIONS = ["전래동화", "판타지", "히어로", "요정", "일상", "자동차", "공주/왕자", "추리", "우주", "로봇", "동물", "공룡"]
PURPOSE_OPTIONS = ["안전 교육", "예절&규칙", "생활 습관", "어휘력 향상", "세계&다양성", "창의력/사고력", "기초과학", "자존감 높이기"]

# ==============================================================================
# 2. 📦 데이터 구조
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
    page_number: int = 0 
    character_name: str = ""
    character_type: str = ""   # 캐릭터 종류 (예: 두루마리 휴지)
    personality: str = ""      # 성격
    magic_power: str = ""      # 능력
    story_narration: str = ""
    dialogue: str = ""
    image: Optional[Image.Image] = None 
    audio_data: Optional[bytes] = None
    is_cover: bool = False 

# ==============================================================================
# 3. 🧠 AI 서비스
# ==============================================================================
class Utils:
    @staticmethod
    def clean_json_text(text):
        text = text.strip()
        if text.startswith("```json"): text = text[7:]
        elif text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        return text.strip()

    @staticmethod
    def image_to_base64(image: Image.Image) -> str:
        if image is None: return ""
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode()

    @staticmethod
    def escape(text: str) -> str:
        """HTML 특수문자 처리"""
        import html
        return html.escape(str(text))

class PhodongService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            st.error("🚨 API Key가 없습니다. .env 파일을 확인해주세요.")
            st.stop()
        
        genai.configure(api_key=self.api_key)
        self.text_model = genai.GenerativeModel(TEXT_MODEL_NAME)
        self.image_model = genai.GenerativeModel(IMAGE_MODEL_NAME)

    def analyze_image(self, image: Image.Image) -> str:
        try:
            res = self.text_model.generate_content(["이 사진에 있는 주요 사물이나 캐릭터가 무엇인지 단답형 한글로 알려줘.", image])
            return res.text.strip()
        except:
            return "알 수 없는 물건"

    def create_character(self, object_desc: str, config: StoryConfig) -> dict:
        prompt = f"""
        '{object_desc}' 사진을 보고 주인공 캐릭터를 설정해주세요.
        - 독자: {config.age}세, 장르: {config.genre}, 목표: {config.purpose}
        [출력 JSON] {{
            "name": "이름 (예: 순결의 롤 대장)", 
            "type": "종류 (예: 두루마리 휴지)",
            "personality": "성격 (한 문장)", 
            "power": "능력 (한 문장)"
        }}
        """
        try:
            res = self.text_model.generate_content(prompt)
            return json.loads(Utils.clean_json_text(res.text))
        except:
            return {"name": "포동이", "type": object_desc, "personality": "용감함", "power": "상상력"}

    def generate_cover_info(self, objects: List[str], config: StoryConfig) -> dict:
        obj_str = ", ".join(objects)
        prompt = f"""
        동화 작가로서 다음 요소들을 포함하는 동화책의 '제목'과 '표지 그림 묘사'를 작성하세요.
        - 등장 사물들: {obj_str}
        - 장르: {config.genre}
        - 독자: {config.child_name} ({config.age}세)
        [출력 JSON] {{"title": "제목", "cover_prompt": "영어 프롬프트"}}
        """
        try:
            res = self.text_model.generate_content(prompt)
            return json.loads(Utils.clean_json_text(res.text))
        except:
            return {"title": "나만의 동화책", "cover_prompt": "Cute adventure, 3d render"}

    def generate_cover_image(self, prompt: str) -> Optional[Image.Image]:
        try:
            response = self.image_model.generate_content(prompt)
            if response.parts:
                return Image.open(io.BytesIO(response.parts[0].inline_data.data))
            return None
        except Exception as e:
            logger.error(f"Image Gen Error: {e}")
            return None

    def generate_page(self, page_num: int, total_pages: int, current_img_desc: str, 
                      character_info: dict, context_so_far: str, config: StoryConfig) -> dict:
        if page_num == 1:
            context_prompt = "이야기의 시작입니다. 주인공을 소개하고 모험을 시작하세요."
        else:
            context_prompt = f"[이전 줄거리]: {context_so_far}\n[현재 상황]: 주인공이 '{current_img_desc}'(을)를 만났습니다. 자연스럽게 이어주세요."

        final_prompt = f"""
        총 {total_pages}페이지 중 {page_num}페이지입니다.
        - 주인공: {character_info['name']}
        - 설정: {config.genre}, {config.purpose}
        - 조건: {config.age}세 아이를 위한 해요체. 지문 3~4문장, 대사 1~2문장.
        {context_prompt}
        [출력 JSON] {{"story_narration": "...", "dialogue": "..."}}
        """
        try:
            res = self.text_model.generate_content(final_prompt)
            return json.loads(Utils.clean_json_text(res.text))
        except:
            return {"story_narration": "...", "dialogue": "..."}

    def text_to_speech(self, text: str) -> Optional[bytes]:
        try:
            if not text: return None
            tts = gTTS(text=text, lang='ko')
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            return mp3_fp.getvalue()
        except:
            return None

    def create_download_html(self, pages: List[StoryCard], config: StoryConfig, title: str) -> str:
        html_content = f"""
        <html><head><meta charset="utf-8">
        <style>body{{font-family:sans-serif;padding:20px;text-align:center;}}.page{{margin-bottom:50px;border:1px solid #eee;padding:20px;border-radius:10px;}}img{{max-width:100%;border-radius:10px;}}</style>
        </head><body><h1>{title}</h1><h3>지은이: {config.child_name}</h3>"""
        for page in pages:
            img_b64 = Utils.image_to_base64(page.image)
            html_content += f"""<div class="page"><img src="data:image/jpeg;base64,{img_b64}"><p>{page.story_narration}</p><p><b>"{page.dialogue}"</b></p></div>"""
        html_content += "</body></html>"
        return html_content

# ==============================================================================
# 4. 🖥️ UI / VIEW LAYER (디자인 핵심 부분)
# ==============================================================================

def init_session_state():
    if "book_pages" not in st.session_state: st.session_state.book_pages = []
    if "book_title" not in st.session_state: st.session_state.book_title = "나만의 동화책"
    if "current_page_idx" not in st.session_state: st.session_state.current_page_idx = 0

def render_book_viewer(config: StoryConfig):
    """[핵심] 보내주신 사진과 동일한 디자인으로 렌더링"""
    pages = st.session_state.book_pages
    idx = st.session_state.current_page_idx
    total = len(pages)
    card = pages[idx]

    # 1. 상단 네비게이션
    st.markdown(styles.Utils.clean_html(f"""
        <div style="display:flex; justify-content:space-between; color:#888; margin-bottom:20px; padding:0 5px; border-bottom: 2px solid #F0F0F0; padding-bottom:10px;">
            <span class='font-heading' style='font-size:1.3rem; color:#FF9EAA;'>📖 {st.session_state.book_title}</span>
            <span class='font-heading' style='font-size:1.1rem; background:#FFF; padding:6px 15px; border:2px solid #F0F0F0; border-radius:15px; color:#A0C4FF;'>
                Page {idx + 1} / {total}
            </span>
        </div>
    """), unsafe_allow_html=True)

    # 2. 메인 콘텐츠 (2컬럼 레이아웃)
    col_img, col_txt = st.columns([1, 1], gap="large")

    # [왼쪽] 폴라로이드 사진 + 캐릭터 프로필 (민트색 박스)
    with col_img:
        # 이미지 Base64 변환
        img_b64 = Utils.image_to_base64(card.image)
        img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else ""
        
        # 렌더링 HTML
        st.markdown(styles.Utils.clean_html(f"""
            <div class='polaroid-frame'>
                <img src='{img_src}' class='polaroid-img'>
                <div class='polaroid-label'>Scene {card.page_number if not card.is_cover else "Cover"}</div>
            </div>
        """), unsafe_allow_html=True)

        # 표지가 아닐 때만 프로필 박스 표시
        if not card.is_cover:
            st.markdown(styles.Utils.clean_html(f"""
                <div class='profile-group'>
                    <span class='badge-pill badge-pink'>✨ {Utils.escape(card.character_name)} ({Utils.escape(card.character_type)})</span>
                    <div style="margin-top:12px;">
                        <span class='badge-pill badge-yellow'>💖 {Utils.escape(card.personality)}</span>
                    </div>
                    <div style="margin-top:12px; font-size: 0.95rem; color: #555; background: #E0F2F1; padding: 8px; border-radius: 8px;">
                        ⚡ {Utils.escape(card.magic_power)}
                    </div>
                </div>
            """), unsafe_allow_html=True)

    # [오른쪽] 대사 (노란색) + 상황설명 (파란색)
    with col_txt:
        st.markdown(styles.Utils.clean_html(f"""
            <div style="padding-top:10px;">
                <div class='dialogue-box'>
                    <div class='dialogue-text'>
                        "{Utils.escape(card.dialogue)}"
                    </div>
                </div>
                
                <div class='context-box'>
                    <strong style='color:#A0C4FF; font-family:"Jua"; display:block; margin-bottom:10px; font-size:1.15rem;'>
                        상황 설명
                    </strong>
                    {Utils.escape(card.story_narration)}
                </div>
            </div>
        """), unsafe_allow_html=True)
        
        # 오디오 플레이어
        if card.audio_data:
            st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
            st.audio(card.audio_data, format='audio/mp3')

    # 3. 하단 버튼 (이전 / 다음 / 전체보기)
    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)
    b_col1, b_col2, b_col3 = st.columns([1, 2, 1])

    with b_col1:
        if idx > 0:
            if st.button("⬅️ 이전", use_container_width=True):
                st.session_state.current_page_idx -= 1
                st.rerun()

    with b_col3:
        if idx < total - 1:
            if st.button("다음 ➡️", use_container_width=True):
                st.session_state.current_page_idx += 1
                st.rerun()
        else:
            # 마지막 페이지면 '전체 보기 및 저장' 버튼
            if st.button("🎁 전체 보기 및 저장", type="primary", use_container_width=True):
                st.session_state.view_mode = "all"
                st.rerun()

def render_all_pages_view(config: StoryConfig):
    """전체 내용을 한 번에 보여주고 저장하는 페이지"""
    st.markdown(f"<h2 class='font-heading' style='text-align:center; color:#FF9EAA; margin-bottom:30px;'>📘 {st.session_state.book_title} (전체 보기)</h2>", unsafe_allow_html=True)
    
    pages = st.session_state.book_pages
    service = PhodongService()

    for page in pages:
        img_b64 = Utils.image_to_base64(page.image)
        st.markdown(styles.Utils.clean_html(f"""
            <div class='content-box' style='margin-bottom: 30px; border-top: 4px solid #FF9EAA;'>
                <div style='text-align:center; margin-bottom:15px; font-family:Jua; color:#A0C4FF; font-size:1.2rem;'>
                    {'🧸 표지' if page.is_cover else f'Page {page.page_number}'}
                </div>
                <img src='data:image/jpeg;base64,{img_b64}' style='width:100%; border-radius:12px; margin-bottom:20px; border:1px solid #EEE;'>
                <div style='background:#FFFBE6; padding:20px; border-radius:15px; margin-bottom:15px; border:1px solid #FFE082;'>
                    <div style='font-family:Jua; font-size:1.3rem; color:#5D4037; margin-bottom:10px;'>"{page.dialogue}"</div>
                    <div style='color:#666; font-size:1rem; line-height:1.6;'>{page.story_narration}</div>
                </div>
            </div>
        """), unsafe_allow_html=True)

    # 다운로드
    st.divider()
    html_data = service.create_download_html(pages, config, st.session_state.book_title)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("💾 HTML로 저장하기", html_data, f"{config.child_name}_story.html", "text/html", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 처음으로", use_container_width=True):
            st.session_state.book_pages = []
            st.session_state.current_page_idx = 0
            st.session_state.view_mode = "single"
            st.rerun()

def main():
    styles.DesignSystem.inject_css()
    init_session_state()
    service = PhodongService()

    # --- 헤더 ---
    st.markdown("""
        <div class="landing-hero" style="text-align:center; padding-bottom: 20px;">
            <h1 class="landing-title">나만의 동화책 만들기</h1>
            <p class="landing-subtitle">사진을 올리면 <b>포동이</b>가 이야기를 만들어줘요!</p>
        </div>
    """, unsafe_allow_html=True)

    # 1. 책이 없을 때 -> 입력 폼
    if not st.session_state.book_pages:
        left_col, right_col = st.columns([1, 1], gap="large")

        with left_col:
            with st.expander("🧸 사용법 보기", expanded=True):
                folder = styles.ArtWork.get_folder(40)
                bear_icon = styles.ArtWork.get_bear(40)
                book = styles.ArtWork.get_book_cover(40)
                st.markdown(styles.Utils.clean_html(f"""
                    <div class="step-container">
                        <div class="step-item step-1">
                            <div>{folder}</div>
                            <div class="step-title" style="color:#A0C4FF;">1. 사진 선택</div>
                            <div class="step-desc">3~5장의 사진을 골라주세요.</div>
                        </div>
                        <div class="step-item step-2">
                            <div>{bear_icon}</div>
                            <div class="step-title" style="color:#FFD580;">2. AI 창작</div>
                            <div class="step-desc">표지 그림과 이야기를 지어줘요.</div>
                        </div>
                        <div class="step-item step-3">
                            <div>{book}</div>
                            <div class="step-title" style="color:#FF9EAA;">3. 책 완성</div>
                            <div class="step-desc">전체 내용을 저장할 수 있어요.</div>
                        </div>
                    </div>
                """), unsafe_allow_html=True)

        with right_col:
            st.markdown(styles.Utils.clean_html("""<div class="landing-action"><div class="action-header">👇 이야기 설정 & 사진 업로드</div>"""), unsafe_allow_html=True)
            
            c_in1, c_in2 = st.columns(2)
            with c_in1: child_name = st.text_input("아이 이름", value="포동이")
            with c_in2: age = st.slider("아이 연령", 3, 9, 5)
            partner_name = st.text_input("함께하는 어른", value="엄마")
            
            c_sel1, c_sel2 = st.columns(2)
            with c_sel1: genre = st.selectbox("장르", GENRE_OPTIONS)
            with c_sel2: purpose = st.selectbox("교육 목표", PURPOSE_OPTIONS)
            
            st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
            
            uploaded_files = st.file_uploader(
                "사진을 순서대로 여러 장 올려주세요! (최대 5장)", 
                type=["jpg", "png", "jpeg"], 
                accept_multiple_files=True,
                label_visibility="collapsed"
            )
            
            process_btn = st.button("✨ 동화책 만들기 시작!", type="primary", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if process_btn:
                if uploaded_files:
                    config = StoryConfig(child_name, partner_name, age, genre, purpose)
                    total_files = len(uploaded_files)
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    temp_book = []
                    context_so_far = "" 
                    character_info = {}
                    
                    try:
                        status_text.markdown("🎨 **동화책 표지를 그리고 있어요...** (잠시만 기다려주세요!)")
                        all_images = [Image.open(f) for f in uploaded_files]
                        
                        # [표지 생성]
                        obj_list = [service.analyze_image(img) for img in all_images[:3]]
                        cover_info = service.generate_cover_info(obj_list, config)
                        st.session_state.book_title = cover_info.get("title", "나만의 동화책")
                        
                        cover_img = service.generate_cover_image(cover_info.get("cover_prompt", ""))
                        if cover_img:
                            temp_book.append(StoryCard(
                                page_number=0, character_name="표지", 
                                story_narration=f"제목: {st.session_state.book_title}", 
                                dialogue=f"지은이: 포동이와 {child_name}", 
                                image=cover_img, is_cover=True
                            ))

                        # [본문 생성]
                        for i, image in enumerate(all_images):
                            current_page = i + 1
                            status_text.markdown(f"**📖 {current_page}번째 페이지 만드는 중...** ({current_page}/{total_files})")
                            
                            obj_desc = obj_list[i] if i < len(obj_list) else service.analyze_image(image)
                            
                            if i == 0:
                                character_info = service.create_character(obj_desc, config)
                            
                            page_data = service.generate_page(
                                page_num=current_page, total_pages=total_files,
                                current_img_desc=obj_desc, character_info=character_info,
                                context_so_far=context_so_far, config=config
                            )
                            
                            audio = service.text_to_speech(page_data['dialogue'])
                            
                            temp_book.append(StoryCard(
                                page_number=current_page,
                                character_name=character_info.get('name', child_name),
                                character_type=character_info.get('type', obj_desc),
                                personality=character_info.get('personality', '-'),
                                magic_power=character_info.get('power', '-'),
                                current_object=obj_desc,
                                story_narration=page_data['story_narration'],
                                dialogue=page_data['dialogue'],
                                image=image,
                                audio_data=audio
                            ))
                            context_so_far += f"\n[Page {current_page}] {page_data['story_narration']}"
                            progress_bar.progress((i + 1) / total_files)
                        
                        st.session_state.book_pages = temp_book
                        st.session_state.config = config
                        st.session_state.view_mode = "single"
                        st.rerun()

                    except Exception as e:
                        st.error(f"에러 발생: {e}")
                else:
                    st.warning("사진을 최소 1장 이상 올려주세요!")

    # 2. 책 완성 -> 뷰어 모드
    else:
        if st.session_state.get("view_mode") == "all":
            render_all_pages_view(st.session_state.config)
        else:
            render_book_viewer(st.session_state.config)

if __name__ == "__main__":
    main()