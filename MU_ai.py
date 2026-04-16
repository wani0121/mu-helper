지완님, 모델을 수동으로 입력하지 않고 자동으로 사용 가능한 모델을 찾아내어 404 에러를 원천 차단하는 로직을 반영했습니다.

이제 이 코드를 사용하면 구글 API가 업데이트되어 모델 이름이 바뀌더라도 에러 없이 작동할 거예요. 아래 코드를 복사해서 mu_ai.py에 통째로 덮어쓰기 해주세요.

⚔️ 최종 수정된 mu_ai.py (채팅형 + 404 에러 자동 방지)
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
st.title("🐲 뮤 온라인 물어보세요")

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

    # 2. AI 답변 생성 (에러 방지 로직 포함)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            # [404 에러 해결] 내 계정에서 사용 가능한 모델 목록을 가져와 자동 선택
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # 'flash' 모델을 우선 찾고, 없으면 목록의 첫 번째 모델 사용
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
            
            # 3. AI 답변 저장
            st.session_state.messages.append({"role": "assistant", "content": ai_answer})
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                st.error("⚠️ 일일 사용량이 소진되었습니다. 잠시 후 다시 시도해 주세요.")
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
