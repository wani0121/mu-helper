import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="AI 기상캐스터", page_icon="🌤️")
st.title("🌤️ AI 기상캐스터")

# 대화 내역 저장
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. 데이터 수집 함수 (최신 네이버 검색 UI 대응) ---
def get_weather(city="서울 날씨"):
    try:
        # 검색어 최적화
        if "날씨" not in city:
            search_city = f"{city} 날씨"
        else:
            search_city = city

        url = f"https://search.naver.com/search.naver?query={search_city}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # [핵심 수정] 네이버 날씨 최신 클래스명 반영
        # 1. 온도 추출
        temp_element = soup.select_one('.temperature_text strong') or \
                       soup.select_one('.todaytemp') or \
                       soup.select_one('.info_data .todaytemp')
        
        if not temp_element:
            return f"'{city}' 지역을 찾을 수 없습니다. '성남시 날씨' 또는 '분당 날씨'처럼 입력해 보세요! 🔍"
        
        # 숫자만 추출
        temp_raw = temp_element.get_text(strip=True)
        temp = "".join(filter(lambda x: x.isdigit() or x == '-', temp_raw))
        
        # 2. 날씨 상태 (맑음, 흐림 등)
        desc_element = soup.select_one('.before_slash') or \
                       soup.select_one('.weather_before_slash') or \
                       soup.select_one('.cast_txt')
        desc = desc_element.get_text(strip=True) if desc_element else "정보 없음"
        
        # 3. 미세먼지 정보
        dust_info = soup.select('.today_chart_list .txt')
        pm10 = dust_info[0].get_text(strip=True) if len(dust_info) > 0 else "보통"
        pm25 = dust_info[1].get_text(strip=True) if len(dust_info) > 1 else "보통"
        
        # 4. 옷차림 추천 로직
        try:
            t_val = float(temp)
            if t_val >= 28: outfit = "매우 더워요! 반팔과 린넨 소재 옷이 필수입니다. ☀️"
            elif t_val >= 23: outfit = "반팔이나 얇은 셔츠를 추천드려요. 에어컨 바람 조심하세요! 👕"
            elif t_val >= 20: outfit = "얇은 긴팔이나 가디건이 적당한 날씨예요. 🧥"
            elif t_val >= 17: outfit = "니트나 맨투맨, 가벼운 자켓을 챙기세요. 👖"
            elif t_val >= 12: outfit = "자켓이나 트렌치코트를 입기 딱 좋아요. 🧣"
            elif t_val >= 9: outfit = "경량 패딩이나 코트로 따뜻하게 입으세요. 🧥"
            elif t_val >= 5: outfit = "겨울 코트나 두꺼운 외투를 추천합니다. 🧤"
            else: outfit = "패딩과 목도리, 장갑으로 무장하세요! 많이 춥습니다. ❄️"
        except:
            outfit = "오늘 기온에 맞는 단정한 옷차림을 추천드려요."

        report = f"""
안녕하세요! AI 기상캐스터입니다. 🎤
요청하신 **{city}**의 실시간 날씨 정보를 전해드립니다!

🌡️ **현재 기온:** {temp}°C ({desc})
😷 **미세먼지:** {pm10} / **초미세먼지:** {pm25}

👗 **오늘의 코디 추천:**
{outfit}

🚀 **외출 팁:**
- 현재 하늘은 {desc} 상태입니다.
- 미세먼지가 '{pm10}' 수준이니 참고해서 이동하세요!
        """
        return report
    except Exception as e:
        return f"날씨 정보를 가져오는 중 기술적 오류가 발생했습니다. 잠시 후 다시 시도해 주세요. 🛠️"

# --- 3. 채팅 화면 표시 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. 채팅 입력 및 로직 ---
if prompt := st.chat_input("지역명을 입력하세요 (예: 성남, 서울, 분당)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        answer = get_weather(prompt)
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

# 사이드바
with st.sidebar:
    st.header("⚙️ 관리 메뉴")
    st.subheader("AI 기상캐스터")
    if st.button('🗑️ 대화 기록 삭제'):
        st.session_state.messages = []
        st.rerun()
