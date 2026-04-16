지완님, 아주 좋은 아이디어입니다! 사용자가 무작정 기다리지 않게 **"잠깐 기다리면 될지(분당 제한), 내일 와야 할지(일일 제한)"**를 AI가 에러 코드를 분석해서 친절하게 알려주도록 코드를 업그레이드했습니다.

요청하신 대로 **용(🐲) 이모티콘은 모두 돋보기(🔍)**로 교체했고, 에러 메시지를 세분화하여 반영한 전체 코드입니다.

🔍 mu_ai.py 전체 코드 (에러 구분 알림 + 돋보기 테마)
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
st.title("🔍 뮤 온라인 물어보세요")

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
            
            # [핵심] 에러 메시지에 따라 알림 구분
            if "429" in error_msg:
                # 429 에러 중 'quota'나 'daily' 문구가 있으면 일일 제한으로 판단
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
