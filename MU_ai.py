import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 1. 설정 및 API 키 ---
try:
    # 기존에 설정해둔 Gemini API 키를 그대로 사용합니다. (두뇌 역할)
    MY_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=MY_API_KEY)
except Exception as e:
    st.error("API 키를 설정해주세요 (Streamlit Secrets).")

# --- 2. 실시간 기상 정보 수집 함수 (오픈소스 크롤링) ---
def get_weather_info(city="서울 날씨"):
    try:
        # 네이버 날씨 검색 결과를 활용하여 무료로 데이터를 가져옵니다.
        url = f"https://search.naver.com/search.naver?query={city}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 현재 온도 및 날씨 상태 추출
        curr_temp = soup.select_one('.temperature_text').text.strip() if soup.select_one('.temperature_text') else "정보 없음"
        weather_desc = soup.select_one('.before_slash').text.strip() if soup.select_one('.before_slash') else "정보 없음"
        
        # 미세먼지 정보 추출
        dust_info = soup.select('.today_chart_list .txt')
        fine_dust = dust_info[0].text if len(dust_info) > 0 else "정보 없음"
        ultra_fine_dust = dust_info[1].text if len(dust_info) > 1 else "정보 없음"
        
        return f"현재 지역: {city}\n상태: {curr_temp}, {weather_desc}\n미세먼지: {fine_dust}\n초미세먼지: {ultra_fine_dust}"
    except Exception as e:
        return f"기상 정보 수집 중 오류가 발생했습니다: {str(e)}"

# --- 3. 페이지 설정 ---
st.set_page_config(page_title="AI 기상캐스터", page_icon="🌤️")
st.title("🌤️ AI 기상캐스터")
st.markdown("오늘부터 모레까지의 날씨와 코디 팁을 친절하게 알려드려요!")

# 대화 내역 저장
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. 채팅 화면 표시 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. 사용자 입력 및 답변 처리 ---
if prompt := st.chat_input("지역 이름이나 날씨 질문을 입력하세요 (예: 서울 날씨 알려줘)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            # 실시간 날씨 데이터 가져오기
            weather_data = get_weather_info()
            
            # AI 모델 설정 (가장 가성비 좋은 1.5-flash 사용)
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model_name = next((m for m in models if '1.5-flash' in m), models[0])
            model = genai.GenerativeModel(model_name)
            
            # 기상캐스터 페르소나 주입
            system_instruction = f"""
            너는 밝고 상냥한 전문 'AI 기상캐스터 샤이니'야. 아래 지침을 따라줘.
            
            [미션]
            1. 제공된 [실시간 기상 데이터]를 바탕으로 오늘, 내일, 모레의 날씨 흐름을 예측해서 알려줘.
            2. 미세먼지 상황에 따른 외출 팁을 포함해줘.
            3. 현재 기온에 맞는 '추천 코디(옷차림)'를 아주 구체적으로 제안해줘.
            4. 말투: 기상캐스터처럼 생동감 넘치고 친절하게, "시청자 여러분" 혹은 "사용자님"이라고 불러줘.
            5. 이모티콘: ☀️, ☁️, 🌧️, ❄️, 💨, 😷 등을 상황에 맞게 많이 사용해줘.
            
            [실시간 기상 데이터]
            {weather_data}
            
            [사용자 질문]
            {prompt}
            """
            
            response = model.generate_content(system_instruction)
            ai_answer = response.text
            
            message_placeholder.markdown(ai_answer)
            st.session_state.messages.append({"role": "assistant", "content": ai_answer})
            
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg:
                st.error("⚠️ 기상 센터 업무량이 많네요! 잠시 후 다시 물어봐 주세요.")
            else:
                st.error(f"방송 사고 발생: {error_msg}")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 서비스 설정")
    st.subheader("AI 기상캐스터 샤이니")
    st.write("실시간 데이터를 기반으로 최적의 옷차림을 추천합니다.")
    
    if st.button('🗑️ 대화 기록 삭제'):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.caption(f"접속 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
