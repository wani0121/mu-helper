import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# --- 1. 설정 및 API 키 ---
# 이 키는 담당자님의 소중한 열쇠입니다!
# 직접 키를 적지 않고, 스트림릿의 'Secrets'라는 비밀 금고에서 가져오게 만듭니다.
MY_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=MY_API_KEY)

# --- 2. [자동 수집 함수] 홈페이지에서 용어 긁어오기 ---
def get_official_terms():
    url = "https://muonline.webzen.co.kr/game-info/guide/library"
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        # 홈페이지의 가이드 리스트 제목(.tit)을 찾아옵니다.
        terms = soup.select('.tit') 
        
        if not terms:
            return "버지드래곤, 로랜시아, 축복의 보석, 흑기사, 날개, 웹젠, 뮤온라인"
            
        collected = ""
        for term in terms:
            collected += f"용어: {term.text.strip()}\n"
        return collected
    except:
        return "기본 데이터: 버지드래곤, 로랜시아, 축복의 보석, 흑기사, 날개"

# --- 3. 웹 화면 구성 ---
st.set_page_config(page_title="뮤 온라인 현지화 조수", page_icon="⚔️")
st.title("🐲 뮤 온라인 현지화 AI 조수")
st.markdown("---")

# 데이터 관리용 저장소 (세션 스테이트)
if 'mu_data' not in st.session_state:
    st.session_state['mu_data'] = "버지드래곤, 로랜시아, 축복의 보석, 흑기사, 날개, 웹젠"

# 버튼을 누르면 홈페이지 데이터를 긁어와서 업데이트합니다.
if st.button('🌐 공식 홈페이지 데이터 동기화'):
    with st.spinner('공식 홈페이지에서 최신 용어를 수집 중입니다...'):
        st.session_state['mu_data'] = get_official_terms()
        st.success('데이터 동기화 완료!')

# --- 4. 사용자 질문 입력창 ---
user_input = st.text_input("질문을 입력하세요", placeholder="예: 버지드래곤에 대해 설명해줘")

if user_input:
    try:
        # [핵심] 에러가 났던 모델 연결 부분을 자동으로 수정하는 로직
        model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # gemini-1.5-flash가 있으면 쓰고, 없으면 리스트의 첫 번째 모델을 사용
        target_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in model_list else model_list[0]
        
        model = genai.GenerativeModel(target_model)
        
        # AI에게 정체성을 부여하는 지침
        prompt = f"""
        너는 웹젠의 '뮤 온라인(奇迹MU)' 전문 현지화 번역가이자 가이드야.
        
        [규칙]
        1. '뮤 온라인'이나 '웹젠'과 상관없는 질문(예: 음식, 날씨, 다른 게임)은 무조건 거절해.
        2. 거절할 때는 "죄송합니다. 저는 뮤 온라인 현지화 관련 답변만 드릴 수 있습니다."라고 말해.
        3. 아래의 [참고 데이터]에 있는 내용을 우선적으로 활용해서 대답해줘.
        
        [참고 데이터]:
        {st.session_state['mu_data']}
        
        사용자 질문: "{user_input}"
        """
        
        response = model.generate_content(prompt)
        
        st.markdown("---")
        st.subheader("💡 AI 번역가의 답변")
        st.write(response.text)
        
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        st.info("API 키 설정이나 모델 연결 상태를 확인해 주세요.")

# 사이드바 (현재 어떤 데이터를 가지고 있는지 확인용)
with st.sidebar:
    st.header("📊 현재 학습 데이터")
    st.caption("공식 홈페이지에서 긁어온 내용들입니다.")
    st.text(st.session_state['mu_data'])