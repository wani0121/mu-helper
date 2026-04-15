담당자님, 에러가 계속되어 정말 고생이 많으십니다. 2026년 현재 구글의 모델 정책이 변경되면서 예전 모델명(1.5-flash)을 찾지 못하는 문제가 발생하고 있는 것 같습니다.

현재 가장 안정적이고 무료 한도가 넉넉한 gemini-2.5-flash 모델을 사용하도록 하고, 모델을 불러오는 방식을 가장 표준적인 형태로 수정한 전체 코드를 드립니다. 이 코드를 복사해서 mu_ai.py에 통째로 덮어쓰기 해주세요.

📝 mu_ai.py 전체 코드 (최종 수정본)
Python
import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# --- 1. 설정 및 API 키 ---
# Streamlit Secrets(비밀 금고)에서 키를 가져옵니다.
try:
    MY_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=MY_API_KEY)
except Exception as e:
    st.error("API 키를 찾을 수 없습니다. Streamlit Settings에서 Secrets 설정을 확인해주세요.")

# --- 2. 공식 홈페이지 데이터 수집 ---
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
st.set_page_config(page_title="뮤 온라인 현지화 조수", page_icon="🐲")
st.title("🐲 뮤 온라인 현지화 AI 조수")

# 세션 상태에 데이터 저장
if 'mu_data' not in st.session_state:
    st.session_state['mu_data'] = "버지드래곤, 로랜시아, 축복의 보석, 흑기사, 날개"

if st.button('🌐 공식 홈페이지 데이터 동기화'):
    with st.spinner('최신 용어 수집 중...'):
        st.session_state['mu_data'] = get_official_terms()
        st.success('동기화 완료!')

# --- 4. 질문 처리 ---
user_input = st.text_input("질문을 입력하세요 (예: 'Lorencia'를 한국어로 뭐야?)")

if user_input:
    try:
        # [수정] 2026년 기준 가장 안정적인 무료 모델명으로 설정합니다.
        # 모델명 앞에 'models/'를 붙여 경로를 명확히 합니다.
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        prompt = f"""
        너는 뮤 온라인(MU Online) 게임의 전문 번역가이자 현지화 전문가야. 
        아래의 공식 용어 데이터를 참고해서 사용자의 질문에 친절하게 답해줘.
        
        [공식 용어 데이터]
        {st.session_state['mu_data']}
        
        [사용자 질문]
        {user_input}
        """
        
        response = model.generate_content(prompt)
        
        if response.text:
            st.info(response.text)
        else:
            st.warning("AI가 답변을 생성하지 못했습니다. 다시 시도해주세요.")
            
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            st.error("⚠️ 무료 사용량이 일시적으로 소진되었습니다. 1분만 기다렸다가 다시 시도해 주세요!")
        elif "404" in error_msg:
            st.error("⚠️ 모델을 찾을 수 없습니다. 모델 이름을 'models/gemini-2.5-flash-lite' 등으로 변경이 필요할 수 있습니다.")
        else:
            st.error(f"오류가 발생했습니다: {error_msg}")

# 사이드바에 현재 참고 데이터 표시
with st.sidebar:
    st.header("설정 및 데이터")
    st.write("현재 학습된 용어 요약:")
    st.caption(st.session_state['mu_data'][:200] + "...")
