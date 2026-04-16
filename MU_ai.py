지완님, 또 제 설명 글이 코드 파일 안에 섞여 들어갔군요! 정말 죄송합니다.

파이썬 파일(.py)은 오로지 컴퓨터가 읽는 명령어만 들어있어야 합니다. 제가 드린 답변의 서론(요청하신 대로... 코드입니다)까지 복사해서 붙여넣으시면, 컴퓨터는 그 한글과 이모지를 읽지 못해 SyntaxError를 냅니다.

🛠️ 해결 방법 (이것만 복사하세요!)
GitHub의 MU_ai.py 편집창에 있는 내용을 전부 지우고, 아래 코드 박스 안에 있는 내용만 첫 줄부터 끝까지 복사해서 붙여넣어 주세요.

※ 주의: import streamlit as st가 반드시 1번 줄에 와야 합니다.

Python
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
st.set_page_config(page_title="뮤 온라인 ai 흑기사", page_icon="🔍")
st.title("🔍 뮤 온라인 ai 흑기사")

# 대화 내역 저장 공간
if "messages" not in st.session_state:
    st.session_state.messages = []

# 뮤 용어 데이터 저장 공간
if 'mu_data' not in st.session_state:
    st.session_state['mu_data'] = "버지드래곤, 로랜시아, 축복의 보석, 흑기사, 날개"

# --- 4. 채팅 화면 표시 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. 사용자 입력 및 답변 처리 ---
if prompt := st.chat_input("질문을 입력하세요..."):
    # 1. 사용자 질문 표시 및 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. AI 답변 생성
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            # 내 계정에서 사용 가능한 모델 목록을 가져와 자동 선택
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model_name = next((m for m in models if 'flash' in m), models[0])
            model = genai.GenerativeModel(model_name)
            
            full_prompt = f"""
            너는 뮤 온라인의 '흑기사' 캐릭터이자 현지화 전문가야.
            
            [규칙]
            1. 형식: [한국어 명칭 | 현지 언어 명칭] 포맷을 사용함.
            2. 말투: 서론/결론 없이 간결하게 답하되, 무뚝뚝하면서도 친절한 흑기사 컨셉 유지.
            
            [데이터] {st.session_state['mu_data']}
            [질문] {prompt}
            """
            
            response = model.generate_content(full_prompt)
            ai_answer = response.text
            
            # 최종 답변 출력
            message_placeholder.markdown(ai_answer)
            st.session_state.messages.append({"role": "assistant", "content": ai_answer})
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # 에러 메시지에 따라 알림 구분
            if "429" in error_msg:
                if "daily" in error_msg or "quota" in error_msg:
                    st.error("⚠️ 오늘 사용량이 모두 소진되었습니다. 내일 다시 시도해주세요.")
                else:
                    st.error("⚠️ 너무 빠르게 질문하셨습니다. 잠시 후 다시 시도해주세요.")
            elif "404" in error_msg:
                st.error("⚠️ 모델을 찾을 수 없습니다. 설정에서 모델명을 확인해주세요.")
            else:
                st.error(f"오류 발생: {error_msg}")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 관리 메뉴")
    if st.button('🌐 데이터 동기화'):
        with st.spinner('수집 중...'):
            st.session_state['mu_data'] = get_official_terms()
            st.success('완료!')
    
    if st.button('🗑️ 대화 기록 삭제'):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.caption("현재 참고 중인 데이터 요약:")
    st.write(st.session_state['mu_data'][:100] + "...")
