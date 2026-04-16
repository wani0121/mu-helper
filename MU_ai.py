import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# --- 1. 설정 및 API 키 ---
try:
    MY_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=MY_API_KEY)
except Exception as e:
    st.error("API 키를 설정해주세요 (Streamlit Secrets).")

# --- 2. 멀티 소스 데이터 수집 함수 ---
def get_combined_data():
    results = []
    
    # 한국 공식 홈페이지 데이터 (수정된 URL)
    try:
        kr_url = "https://www.muonline.co.kr/main"
        # 브라우저처럼 보이게 하기 위한 헤더 추가 (수집 성공률 향상)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        kr_res = requests.get(kr_url, headers=headers, timeout=5)
        kr_res.encoding = 'utf-8'
        kr_soup = BeautifulSoup(kr_res.text, 'html.parser')
        
        # 메인 페이지에서 텍스트 요소 추출 (공지사항, 메뉴 등)
        kr_elements = kr_soup.find_all(['a', 'span', 'strong', 'p'], limit=100)
        kr_text = "\n".join(list(set([t.text.strip() for t in kr_elements if len(t.text.strip()) > 1])))
        results.append("### [한국 공식 데이터 (muonline.co.kr)]\n" + kr_text)
    except Exception as e:
        results.append(f"한국 데이터 수집 실패: {str(e)}")

    # 중국 현지 사이트 데이터 (mu.dvg.cn)
    try:
        cn_url = "https://mu.dvg.cn/"
        cn_res = requests.get(cn_url, timeout=5)
        cn_res.encoding = 'utf-8'
        cn_soup = BeautifulSoup(cn_res.text, 'html.parser')
        cn_elements = cn_soup.find_all(['a', 'span'], limit=100) 
        cn_text = "\n".join(list(set([t.text.strip() for t in cn_elements if len(t.text.strip()) > 1])))
        results.append("\n### [중국 현지 데이터 (mu.dvg.cn)]\n" + cn_text)
    except Exception as e:
        results.append(f"중국 데이터 수집 실패: {str(e)}")
        
    return "\n".join(results)

# --- 3. 페이지 설정 ---
st.set_page_config(page_title="뮤온라인 ai 흑기사", page_icon="🔍")
st.title("🔍 뮤온라인 ai 흑기사")

if "messages" not in st.session_state:
    st.session_state.messages = []

if 'mu_data' not in st.session_state:
    st.session_state['mu_data'] = "사이드바에서 '데이터 동기화' 버튼을 눌러 최신 정보를 가져오세요."

# --- 4. 채팅 화면 표시 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. 사용자 입력 및 답변 처리 ---
if prompt := st.chat_input("질문을 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            # 사용 가능한 모델 목록 확인
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model_name = next((m for m in models if '1.5-flash' in m), models[0])
            model = genai.GenerativeModel
