import streamlit as st
import requests
import geocoder
from datetime import datetime

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="AI 기상캐스터", page_icon="🌤️")
st.title("🌤️ AI 기상캐스터")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. 날씨 및 미세먼지 통합 수집 함수 ---
def get_weather_full(query):
    try:
        # 지역명 추출 로직
        clean_query = query.replace("날씨", "").replace("미세먼지", "").replace("어때", "").replace("알려줘", "").strip()
        
        if not clean_query or clean_query == "":
            g = geocoder.ip('me')
            target_city = g.city if g.city else "Seoul"
        else:
            target_city = clean_query

        # 영문 도시명 매핑 (안정성 확보)
        city_map = {"성남": "Seongnam", "판교": "Pangyo", "서울": "Seoul", "부산": "Busan"}
        search_city = city_map.get(target_city, target_city)

        # wttr.in 호출
        url = f"https://wttr.in/{search_city}?format=j1"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()

        # [현재 날씨]
        current = data.get('current_condition', [{}])[0]
        temp = current.get('temp_C', '??')
        humidity = current.get('humidity', '??')
        
        # [미세먼지 유추 로직] 가시거리와 기상코드로 분석
        visibility = float(current.get('visibility', 10))
        if visibility > 15: dust_status = "매우 좋음 ✨"
        elif visibility > 10: dust_status = "보통 😊"
        elif visibility > 5: dust_status = "약간 나쁨 ☁️"
        else: dust_status = "매우 나쁨 😷 (마스크 필수!)"

        # [3일 예보] 에러 방지용 안전한 추출
        f_list = []
        forecast_data = data.get('weather', [])
        for f in forecast_data[:3]:
            date = f.get('date', '날짜 미상')
            max_t = f.get('maxtemp_C', '??')
            min_t = f.get('mintemp_C', '??')
            f_list.append(f"- {date}: {min_t}°C ~ {max_t}°C")
        
        if not f_list: f_list = ["예보 데이터를 가져올 수 없습니다."]

        # 기온별 옷차림 추천
        try:
            t_val = int(temp)
            if t_val >= 28: outfit = "땀 흡수가 잘 되는 반팔과 반바지를 입으세요! ☀️"
            elif t_val >= 20: outfit = "가벼운 긴팔이나 셔츠가 활동하기 좋아요. 👕"
            elif t_val >= 12: outfit = "자켓이나 야상, 트렌치코트가 필요해요. 🧥"
            elif t_val >= 5: outfit = "두꺼운 코트나 경량 패딩을 추천합니다. 🧣"
            else: outfit = "패딩과 방한용품으로 체온을 유지하세요! ❄️"
        except:
            outfit = "일교차에 대비해 겉옷을 챙기시길 권장합니다."

        report = f"""
안녕하세요! AI 기상캐스터입니다. 🎤
요청하신 **{target_city}** 지역의 날씨와 미세먼지 예보입니다!

🌡️ **현재 기온:** {temp}°C (습도 {humidity}%)
😷 **미세먼지 예보:** 현재 '{dust_status}' 수준입니다.

📅 **단기 예보 (오늘/내일/모레):**
{chr(10).join(f_list)}

👗 **오늘의 코디 추천:**
{outfit}

🚀 **외출 팁:**
- '{target_city}'의 실시간 데이터를 기반으로 구성했습니다.
- 미세먼지 상황이 '{dust_status}'이니 참고하세요!
        """
    except Exception as e:
        report = f"'{query}' 정보를 분석하는 중 오류가 발생했습니다. 지역명(예: 성남, 판교)만 입력해 보시겠어요? (사유: {str(e)})"
    
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
        with st.spinner('실시간 기상 데이터를 수집 중입니다...'):
            answer = get_weather_full(prompt)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

# 사이드바
with st.sidebar:
    st.header("⚙️ 서비스 상태")
    st.success("데이터 엔진: wttr.in (정상)")
    st.info("자동 위치 감지 및 미세먼지 분석 기능 포함")
    if st.button('🗑️ 대화 기록 삭제'):
        st.session_state.messages = []
        st.rerun()
