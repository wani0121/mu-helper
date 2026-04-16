import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# --- 1. 설정 및 API 키 ---
try:
    MY_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=MY_API_KEY)
except Exception as e:
    st.error("API 키를 설정해주세요.")

# --- 2. 데이터 수집 함수 ---
def get_official_terms():
    url = "https://muonline.webzen.co.kr/game-info/guide/library"
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        terms = soup.select('.tit')
        return "\n".join([f"용어: {t.text.strip()}" for t in terms]) if terms else "기본 데이터 없음"
    except:
        return "데이터 수집 실패"

# --- 3. 페이지 설정 ---
st.set_page_config(page_title="뮤 온라인 현지화 조수", page_icon="🔍")
st.title("🔍 뮤 온라인:ai흑기사")

# [중요] 대화 내역을 저장할 공간 만들기
if "messages" not in st.session_state:
    st.session_state.messages = []

if 'mu_data' not in st.session_state:
    st.session_state['mu_data'] = "버지드래곤, 로랜시아, 축복의 보석, 흑기사, 날개"

# --- 4. 채팅 화면 표시 ---
# 저장된 모든 대화 내용을 화면에 뿌려줍니다.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. 사용자 입력 및 답변 처리 ---
if prompt := st.chat_input("질문을 입력하세요..."):
    # 1. 사용자 질문을 화면에 표시하고 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. AI 답변 생성
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
        # 1. 내 계정에서 사용 가능한 최신 모델 목록을 가져옵니다.
        available_models = [m.name for m in genai.list_models() 
                            if 'generateContent' in m.supported_generation_methods]
        
        # 2. 'gemini-2.5-flash', 'gemini-1.5-flash' 등 사용 가능한 모델 중 하나를 선택합니다.
        # 목록 중 가장 첫 번째 모델을 쓰거나, 'flash'가 포함된 모델을 우선 선택합니다.
        model_name = next((m for m in available_models if 'flash' in m), available_models[0])
        
        model = genai.GenerativeModel(model_name)
        
        # [참고] 현재 선택된 모델명을 화면에 작게 표시해서 확인해볼 수 있습니다.
        # st.caption(f"현재 작동 중인 모델: {model_name}")
        
        prompt = f"""
        너는 뮤 온라인의 '흑기사' 캐릭터이자 현지화 전문가야.
        [규칙]
        1. 형식: [한국어 명칭 | 현지 언어 명칭] 포맷 사용.
        2. 말투: 간결하게 정보만 전달.
        
        [데이터] {st.session_state['mu_data']}
        [질문] {user_input}
        """
        
        response = model.generate_content(prompt)
            ai_answer = response.text
            
            message_placeholder.markdown(ai_answer)
            # 3. AI 답변을 저장
            st.session_state.messages.append({"role": "assistant", "content": ai_answer})
            
        except Exception as e:
            st.error(f"오류 발생: {e}")

# 사이드바 설정
with st.sidebar:
    if st.button('🌐 데이터 동기화'):
        st.session_state['mu_data'] = get_official_terms()
        st.success('완료!')
    if st.button('🗑️ 대화 기록 삭제'):
        st.session_state.messages = []
        st.rerun()
