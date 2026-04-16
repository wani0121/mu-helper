import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="AI 기상캐스터", page_icon="🌤️")
st.title("🌤️ AI 기상캐스터")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. 데이터 수집 함수 (가장 확실한 네이버 크롤링) ---
def get_weather_naver(query):
    try:
        # 검색어 다듬기 (예: '성남 날씨 알려줘' -> '성남 날씨')
        if "날씨" not in query and "미세먼지" not in query:
            search_query = f"{query} 날씨"
        else:
            search_query = query

        url = f"https://search.naver.com/search.naver?query={search_query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')

        # [필독] 네이버 구조에 맞춘 정밀 수집
        # 1. 현재 온도
        temp = soup.select_one('.temperature_text strong').get_text(strip=True).replace('현재 온도', '') if soup.select_one('.temperature_text strong') else "정보 없음"
        
        # 2. 날씨 상태 (흐림, 맑음 등)
        desc = soup.select_one('.before_slash').get_text(strip=True) if soup.select_one('.before_slash') else "정보 없음"
        
        # 3. 미세먼지 수치
        dust_info = soup.select('.today_chart_list .txt')
        pm10 = dust_info[0].get_text(strip=True) if len(dust_info) > 0 else "보통"
        pm25 = dust_info[1].get_text(strip=True) if len(dust_info) > 1 else "보통"
        
        # 4. 내일/모레 예보 (?? 방지)
        # 네이버 날씨 하단의 '시간대별/주간' 데이터를 가져옵니다.
        forecast_items = soup.select('.week_item')
        f_list = []
        for item in forecast_items[:3]: # 오늘, 내일, 모레
            day = item.select_one('.day').text.strip()
            min_t = item.select_one('.lowest').text.replace('최저기온', '').strip()
            max_t = item.select_one('.highest').text.replace('최고기온', '').strip()
            f_list.append(f"- {day}: {min_t} / {max_t}")

        # 기온별 코디 추천 (t_val 추출)
        try:
            t_val = float("".join(filter(lambda x: x.isdigit() or x == '.', temp)))
            if t_val >= 28: outfit = "반팔과 시원한 소재가 필수! ☀️"
            elif t_val >= 20: outfit = "가벼운 가디건이나 긴팔 티셔츠! 👕"
            elif t_val >= 12: outfit = "자켓이나 트렌치코트를 챙기세요. 🧥"
            elif t_val >= 5: outfit = "코트나 두꺼운 외투가 필요해요. 🧣"
            else: outfit = "패딩과 목도리로 무장하세요! ❄️"
        except:
            outfit = "일교차를 고려해 겉옷을 준비하세요."

        report = f"""
안녕하세요! AI 기상캐스터입니다. 🎤
요청하신 **{query}** 실시간 브리핑입니다!

🌡️ **현재 기온:** {temp} ({desc})
😷 **미세먼지:** {pm10} / **초미세먼지:** {pm25}

📅 **단기 예보 (오늘/내일/모레):**
{chr(10).join(f_list) if f_list else "네이버에서 예보 데이터를 찾는 중입니다..."}

👗 **오늘의 코디 추천:**
{outfit}

🚀 **외출 팁:**
- 현재 하늘은 {desc} 상태입니다.
- 미세먼지가 '{pm10}' 수준이니 참고해서 이동하세요!
        """
        return report
    except Exception as e:
        return f"날씨 정보를 가져오는 중 오류가 발생했습니다. '성남'이나 '판교 날씨'처럼 다시 입력해 보세요! (사유: {str(e)})"

# --- 3. 채팅 화면 표시 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. 채팅 입력창 ---
if prompt := st.chat_input("지역을 입력하세요 (예: 성남 날씨, 판교 미세먼지)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner('실시간 기상 데이터를 수집 중입니다...'):
            answer = get_weather_naver(prompt)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

# 사이드바
with st.sidebar:
    st.header("⚙️ 관리 메뉴")
    st.info("실시간 네이버 날씨 데이터 연동 중")
    if st.button('🗑️ 대화 기록 삭제'):
        st.session_state.messages = []
        st.rerun()
