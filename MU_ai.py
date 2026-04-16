import streamlit as st
import requests
from datetime import datetime

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="AI 기상캐스터", page_icon="🌤️")
st.title("🌤️ AI 기상캐스터")

# 대화 내역 저장
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. 안정적인 날씨 데이터 수집 함수 (wttr.in 사용) ---
def get_weather_stable(city_name):
    try:
        # 영문 지역명 매핑 (안정적인 조회를 위해)
        city_map = {
            "서울": "Seoul", "성남": "Seongnam", "분당": "Bundang", 
            "부산": "Busan", "인천": "Incheon", "대구": "Daegu", 
            "대전": "Daejeon", "광주": "Gwangju", "수원": "Suwon"
        }
        
        # 입력된 한글에서 지역명만 추출
        clean_name = city_name.replace("날씨", "").strip()
        eng_city = city_map.get(clean_name, clean_name)

        # wttr.in API 호출 (JSON 형식으로 데이터 수집)
        url = f"https://wttr.in/{eng_city}?format=j1"
        res = requests.get(url, timeout=10)
        data = res.json()

        # 데이터 파싱
        current = data['current_condition'][0]
        temp = current['temp_C']
        desc_en = current['weatherDesc'][0]['value']
        
        # 날씨 상태 한글화
        weather_dict = {
            "Sunny": "맑음 ☀️", "Clear": "맑음 ☀️", "Partly cloudy": "구름 조금 ⛅",
            "Cloudy": "흐림 ☁️", "Overcast": "매우 흐림 ☁️", "Mist": "안개 🌫️",
            "Patchy rain possible": "비 올 가능성 🌧️", "Light rain": "약한 비 🌧️"
        }
        desc_kr = weather_dict.get(desc_en, desc_en)

        # 기온별 코디 로직
        t_val = int(temp)
        if t_val >= 28: outfit = "반팔과 린넨 소재가 필수인 무더위예요! ☀️"
        elif t_val >= 20: outfit = "얇은 가디건이나 긴팔 티셔츠가 적당해요. 🧥"
        elif t_val >= 12: outfit = "자켓이나 트렌치코트를 챙기시는 게 좋겠어요. 🧣"
        elif t_val >= 5: outfit = "코트나 두꺼운 외투를 입어야 할 날씨입니다. 🧤"
        else: outfit = "매우 추워요! 패딩과 목도리로 무장하세요! ❄️"

        report = f"""
안녕하세요! AI 기상캐스터입니다. 🎤
요청하신 **{clean_name}** 지역의 날씨입니다!

🌡️ **현재 기온:** {temp}°C
🌈 **날씨 상태:** {desc_kr}

👗 **오늘의 코디 추천:**
{outfit}

🚀 **외출 팁:**
- 현재 기온이 {temp}도이니 참고해서 옷차림을 결정하세요!
- 건강한 하루 보내시길 바랍니다! 🍀
        """
        return report

    except Exception as e:
        return f"죄송합니다. '{city_name}' 정보를 가져오지 못했습니다. 지역명을 '서울'이나 'Seongnam'처럼 입력해 보세요! (오류: {str(e)})"

# --- 3. 채팅 화면 표시 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. 채팅 입력 및 로직 ---
if prompt := st.chat_input("지역명을 입력하세요 (예: 성남, 서울)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner('기상 데이터를 분석 중입니다...'):
            answer = get_weather_stable(prompt)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

# 사이드바
with st.sidebar:
    st.header("⚙️ 관리 메뉴")
    if st.button('🗑️ 대화 기록 삭제'):
        st.session_state.messages = []
        st.rerun()
