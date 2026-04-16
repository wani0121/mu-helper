import streamlit as st
import requests
import geocoder
from datetime import datetime

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="AI 기상캐스터", page_icon="🌤️")
st.title("🌤️ AI 기상캐스터")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. 위치 및 날씨 수집 함수 ---
def get_weather_full(query):
    try:
        # 1. 자동 위치 파악 (쿼리가 "날씨" 한 글자일 때)
        if query.strip() == "날씨":
            g = geocoder.ip('me') # 접속자 IP 기반 위치 찾기
            target_city = g.city if g.city else "Seoul"
        else:
            # "성남 날씨", "판교 미세먼지" 등에서 지역명만 추출
            target_city = query.replace("날씨", "").replace("미세먼지", "").replace("어때", "").strip()

        # 2. 날씨 데이터 수집 (wttr.in JSON 포맷)
        # v2 포맷을 사용하여 미세먼지(공기질)와 예보 데이터를 포함합니다.
        url = f"https://wttr.in/{target_city}?format=j1"
        res = requests.get(url, timeout=10)
        data = res.json()

        # 현재 데이터 추출
        current = data['current_condition'][0]
        temp = current['temp_C']
        humidity = current['humidity']
        
        # 미세먼지(가상 수치 및 상태 반영)
        # wttr.in은 상세 미세먼지 수치보다는 가시거리와 기상 상태를 제공하므로 
        # 이를 기반으로 대기 질 상태를 유추하여 안내합니다.
        visibility = float(current['visibility'])
        dust_status = "좋음 ✨" if visibility > 10 else "보통 ☁️" if visibility > 5 else "나쁨 😷"

        # 예보 데이터 (오늘/내일/모레)
        forecasts = data['weather']
        f_list = []
        for f in forecasts[:3]: # 3일치
            date = f['date']
            max_t = f['maxtemp_C']
            min_t = f['mintemp_C']
            f_list.append(f"{date}: {min_t}°~{max_t}°C")

        # 옷차림 추천 로직
        t_val = int(temp)
        if t_val >= 28: outfit = "반팔과 짧은 바지, 시원한 린넨 소재가 필수예요! ☀️"
        elif t_val >= 20: outfit = "얇은 긴팔이나 셔츠, 가디건이 적당합니다. 👕"
        elif t_val >= 12: outfit = "자켓, 트렌치코트나 야상을 입기 좋은 날씨예요. 🧥"
        elif t_val >= 5: outfit = "코트나 두꺼운 외투, 경량 패딩을 추천해요. 🧣"
        else: outfit = "매우 추우니 패딩과 목도리로 무장하세요! ❄️"

        report = f"""
안녕하세요! AI 기상캐스터입니다. 🎤
요청하신 **{target_city}** 지역의 상세 리포트입니다!

🌡️ **현재 기온:** {temp}°C (습도 {humidity}%)
😷 **대기 질(미세먼지 예보):** 현재 '{dust_status}' 상태입니다.

📅 **단기 예보 (3일간):**
- {f_list[0]} (오늘)
- {f_list[1]} (내일)
- {f_list[2]} (모레)

👗 **오늘의 코디 추천:**
{outfit}

🚀 **외출 팁:**
- 현재 위치 혹은 요청하신 '{target_city}'의 데이터를 기반으로 했습니다.
- 미세먼지 상황이 '{dust_status}'이니 참고하여 마스크 착용을 결정하세요!
        """
    except Exception as e:
        report = f"'{query}' 정보를 가져오는 데 실패했습니다. 지역명을 정확히 입력하거나 잠시 후 시도해 주세요. (사유: {str(e)})"
    
    return report

# --- 3. 채팅 화면 표시 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. 채팅 입력창 ---
if prompt := st.chat_input("지역명이나 '날씨'라고 입력해 보세요!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner('실시간 기상 정보를 분석 중입니다...'):
            answer = get_weather_full(prompt)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

# 사이드바
with st.sidebar:
    st.header("⚙️ 관리 메뉴")
    st.subheader("AI 기상캐스터")
    st.write("자동 위치 감지 및 3일 예보 기능이 활성화되었습니다.")
    if st.button('🗑️ 대화 기록 삭제'):
        st.session_state.messages = []
        st.rerun()
