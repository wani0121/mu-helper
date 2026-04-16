import streamlit as st
import requests
from datetime import datetime

# --- 1. 설정 및 API 키 (변수명 통일) ---
# Streamlit Secrets에 OPENWEATHER_API_KEY로 저장되어 있어야 합니다.
if "OPENWEATHER_API_KEY" in st.secrets:
    API_KEY = st.secrets["OPENWEATHER_API_KEY"]
else:
    API_KEY = None
    st.warning("⚠️ API 키가 설정되지 않았습니다. 사이드바나 Secrets 설정을 확인해주세요.")

# --- 2. 데이터 수집 함수 (OpenWeatherMap 오픈 소스 활용) ---
def get_weather_api(city_name):
    if not API_KEY:
        return "서비스 준비 중입니다. API 키 설정을 확인해주세요."

    try:
        # 1. 도시 이름 정리 (한글 -> 영문 변환)
        city_map = {
            "성남": "Seongnam", "판교": "Seongnam", "서울": "Seoul", 
            "부산": "Busan", "인천": "Incheon", "대구": "Daegu"
        }
        # 사용자가 '성남 날씨'라고 입력해도 '성남'만 추출
        clean_name = city_name.replace("날씨", "").replace("미세먼지", "").strip()
        eng_city = city_map.get(clean_name, clean_name)

        # 2. 실시간 날씨 호출 (OpenWeatherMap API)
        url = f"https://api.openweathermap.org/data/2.5/weather?q={eng_city}&appid={API_KEY}&units=metric&lang=kr"
        res = requests.get(url, timeout=5)
        data = res.json()

        if data.get("cod") != 200:
            return f"'{city_name}' 지역을 찾을 수 없습니다. (영문명: {eng_city})"

        # 3. 데이터 파싱
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind = data['wind']['speed']

        # 4. 옷차림 추천 로직 (기온 기반)
        if temp >= 28: outfit = "매우 더워요! 반팔, 반바지, 린넨 소재가 필수입니다. ☀️"
        elif temp >= 20: outfit = "가벼운 가디건이나 긴팔 티셔츠를 추천드려요. 👕"
        elif temp >= 12: outfit = "자켓, 트렌치코트나 야상을 입기 좋은 날씨예요. 🧥"
        elif temp >= 5: outfit = "코트나 두꺼운 외투, 경량 패딩을 입으세요. 🧣"
        else: outfit = "많이 춥습니다! 패딩과 목도리로 무장하세요! ❄️"

        # 답변 구성
        report = f"""
안녕하세요! AI 기상캐스터입니다. 🎤
오픈 소스 데이터를 기반으로 분석한 **{clean_name}** 지역 날씨입니다!

🌡️ **현재 기온:** {temp}°C ({desc})
💨 **풍속/습도:** {wind}m/s / {humidity}%

👗 **오늘의 코디 추천:**
{outfit}

📅 **단기 안내:**
- 현재 외부 상태는 '{desc}'입니다.
- 일교차에 주의하시고 행복한 하루 보내세요! 🍀
        """
        return report

    except Exception as e:
        return f"데이터를 가져오는 중 오류가 발생했습니다. (사유: {str(e)})"

# --- 3. 채팅 UI 설정 ---
st.set_page_config(page_title="AI 기상캐스터", page_icon="🌤️")
st.title("🌤️ AI 기상캐스터")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("지역을 입력하세요 (예: 성남, 서울 날씨)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner('실시간 기상 정보를 불러오는 중...'):
            answer = get_weather_api(prompt)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

# 사이드바
with st.sidebar:
    st.header("⚙️ 관리 메뉴")
    if st.button('🗑️ 대화 기록 삭제'):
        st.session_state.messages = []
        st.rerun()
