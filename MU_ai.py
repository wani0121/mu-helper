import streamlit as st
import requests
from datetime import datetime, timedelta

# --- 1. 설정 및 API 키 ---
# https://openweathermap.org/ 에 가입 후 발급받은 API 키를 st.secrets에 넣으세요.
try:
    WEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
except:
    st.warning("공종 데이터 API 키가 설정되지 않았습니다. (Streamlit Secrets)")

# --- 2. 데이터 수집 함수 (OpenWeatherMap API) ---
def get_weather_data(city_name):
    try:
        # 한글 도시명을 영문으로 매핑 (API 인식용)
        city_map = {"성남": "Seongnam", "판교": "Seongnam", "서울": "Seoul", "부산": "Busan"}
        eng_city = city_map.get(city_name.replace(" ", ""), city_name)

        # 1. 현재 날씨 및 미세먼지(Air Quality) 가져오기
        # 현재 날씨 URL
        curr_url = f"https://api.openweathermap.org/data/2.5/weather?q={eng_city}&appid={WEATHER_API_KEY}&units=metric&lang=kr"
        curr_res = requests.get(curr_url).json()
        
        lat, lon = curr_res['coord']['lat'], curr_res['coord']['lon']
        
        # 미세먼지 URL (위도, 경도 기반)
        air_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}"
        air_res = requests.get(air_url).json()

        # 2. 데이터 파싱
        temp = curr_res['main']['temp']
        desc = curr_res['weather'][0]['description']
        humidity = curr_res['main']['humidity']
        
        # 미세먼지 지수 (1: 좋음 ~ 5: 매우 나쁨)
        aqi = air_res['list'][0]['main']['aqi']
        aqi_map = {1: "매우 좋음 ✨", 2: "좋음 😊", 3: "보통 ☁️", 4: "나쁨 😷", 5: "매우 나쁨 🚨"}
        dust_status = aqi_map.get(aqi, "정보 없음")

        # 3. 옷차림 추천
        if temp >= 28: outfit = "반팔과 린넨 소재가 필수인 무더위예요! ☀️"
        elif temp >= 20: outfit = "가벼운 가디건이나 긴팔 티셔츠가 적당해요. 👕"
        elif temp >= 12: outfit = "자켓이나 트렌치코트를 챙기시는 게 좋겠어요. 🧣"
        elif temp >= 5: outfit = "코트나 두꺼운 외투를 입어야 할 날씨입니다. 🧤"
        else: outfit = "매우 추워요! 패딩과 목도리로 무장하세요! ❄️"

        report = f"""
안녕하세요! AI 기상캐스터입니다. 
오픈소스 API로 분석한 **{city_name}** 지역의 날씨입니다!

🌡️ **현재 기온:** {temp}°C ({desc})
😷 **미세먼지 상태:** {dust_status} (습도 {humidity}%)

👗 **오늘의 코디 추천:**
{outfit}

📅 **안내사항:**
- 위 정보는 글로벌 기상 관측망(OpenWeather) 데이터를 기반으로 합니다.
- 미세먼지 수치가 '{dust_status}'이니 참고하여 외출하세요!
        """
        return report
    except Exception as e:
        return f"날씨 정보를 가져오지 못했습니다. API 키를 확인하거나 지역명을 다시 입력해 보세요. (사유: {str(e)})"

# --- 3. Streamlit UI ---
st.title("🌤️ AI 기상캐스터 (OpenSource API)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("지역을 입력하세요 (예: 성남, 서울)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        answer = get_weather_data(prompt)
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
