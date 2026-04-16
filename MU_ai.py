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
    
    # 한국 공식 홈페이지 데이터
    try:
        kr_url = "https://www.muonline.co.kr/main"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        kr_res = requests.get(kr_url, headers=headers, timeout=5)
        kr_res.encoding = 'utf-8'
        kr_soup = BeautifulSoup(kr_res.text, 'html.parser')
        kr_elements = kr_soup.find_all(['a', 'span', 'strong', 'p'], limit=100)
        kr_text = "\n".join(list(set([t.text.strip() for t in kr_elements if len(t.text.strip()) > 1])))
        results.append("### [한국 공식 데이터]\n" + kr_text)
    except Exception as e:
        results.append(f"한국 데이터 수집 실패: {str(e)}")

    # 중국 현지 사이트 데이터
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
        # [수정 포인트] try-except 구문을 명확하게 닫았습니다.
        try:
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model_name = next((m for m in models if '1.5-flash' in m), models[0])
            model = genai.GenerativeModel(model_name)
            
            full_prompt = f"""
            너는 한국 '뮤 온라인' 공식 사이트와 중국 '奇迹MU(mu.dvg.cn)' 사이트 데이터를 대조 분석하는 현지화 전문가 흑기사야.
            
            [미션]
            제공된 데이터를 바탕으로 한국 서비스 명칭과 중국 현지 명칭의 차이를 설명해줘. 
            데이터가 부족해도 네 지식을 활용해 답해라.
            
            [규칙]
            1. 형식: [한국어 명칭 | 중국어 명칭(현지어)] 포맷 사용.
            2. 말투: 간결하고 무뚝뚝한 흑기사 컨셉.
            
            [참고 데이터]
            {st.session_state['mu_data']}
            
            [사용자 질문]
            {prompt}
            """
            
            response = model.generate_content(full_prompt)
            ai_answer = response.text
            message_placeholder.markdown(ai_answer)
            st.session_state.messages.append({"role": "assistant", "content": ai_answer})
            
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg:
                if "daily" in error_msg or "quota" in error_msg:
                    st.error("⚠️ 오늘 사용량이 모두 소진되었습니다. 내일 다시 시도해주세요.")
                else:
                    st.error("⚠️ 너무 빠르게 질문하셨습니다. 잠시 후 다시 시도해주세요.")
            else:
                st.error(f"오류 발생: {error_msg}")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 관리 메뉴")
    st.subheader("뮤온라인 ai 흑기사")
    
    if st.button('🌐 데이터 동기화 (KR/CN)'):
        with st.spinner('데이터 수집 중...'):
            st.session_state['mu_data'] = get_combined_data()
            st.success('동기화 완료!')
    
    if st.button('🗑️ 대화 기록 삭제'):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.caption("수집된 데이터 요약:")
    st.write(st.session_state['mu_data'][:150] + "...")
