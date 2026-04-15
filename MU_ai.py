import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# --- 1. 설정 및 API 키 ---
# Streamlit Secrets에서 키를 가져옵니다. (GitHub에는 노출 안 됨)
MY_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=MY_API_KEY)

# --- 2. 공식 홈페이지 데이터 수집 (기존과 동일) ---
def get_official_terms():
    url = "https://muonline.webzen.co.kr/game-info/guide/library"
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        terms = soup.select('.tit') 
        if not terms:
            return "버지드래곤, 로랜시아, 축복의 보석, 흑기사, 날개"
        return "\n".join([f"용어: {t.text.strip()}" for t in terms])
    except:
        return "기본 데이터: 버지드래곤, 로랜시아, 축복의 보석"

# --- 3. 웹 화면 구성 ---
st.set_page_config(page_title="뮤 온라인 현지화 조수", page_icon="🚀")
st.title("🚀 뮤 온라인 현지화 AI 조수")

if 'mu_data' not in st.session_state:
    st.session_state['mu_data'] = "버지드래곤, 로랜시아, 축복의 보석, 흑기사, 날개"

if st.button('🌐 공식 홈페이지 데이터 동기화'):
    with st.spinner('수집 중...'):
        st.session_state['mu_data'] = get_official_terms()
        st.success('완료!')

# --- 4. 질문 처리 ---
user_input = st.text_input("질문을 입력하세요")

if user_input:
    try:
        # [수정] 무료 한도가 가장 넉넉한 1.5-flash 모델로 이름을 정확히 고정합니다.
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        너는 뮤 온라인 전문 번역가야. 아래 데이터를 참고해서 답해줘.
        데이터: {st.session_state['mu_data']}
        질문: {user_input}
        """
        
        response = model.generate_content(prompt)
        st.info(response.text)
        
    except Exception as e:
        # 과금/한도 에러(429) 발생 시 알기 쉽게 안내
        if "429" in str(e):
            st.error("⚠️ 무료 사용량이 일시적으로 소진되었습니다. 1분만 기다렸다가 다시 시도해 주세요!")
        else:
            st.error(f"오류가 발생했습니다: {e}")

with st.sidebar:
    st.write("학습 데이터:", st.session_state['mu_data'])
# 사이드바 (현재 어떤 데이터를 가지고 있는지 확인용)
with st.sidebar:
    st.header("📊 현재 학습 데이터")
    st.caption("공식 홈페이지에서 긁어온 내용들입니다.")
    st.text(st.session_state['mu_data'])
