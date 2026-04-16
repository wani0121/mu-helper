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

# --- 2. 데이터 수집 함수 (보강된 크롤링 로직) ---
def get_weather(city="서울 날씨"):
    try:
        url = f"https://search.naver.com/search.naver?query={city}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. 기온 추출 (다양한 클래스 대응)
        temp_element = soup.select_one('.temperature_text strong') or soup.select_one('.todaytemp') or soup.select_one('._today_temp')
        if not temp_element:
            return f"'{city}'의 날씨 정보를 찾을 수 없습니다. 지역명을 정확히 입력해 주세요! 🔍"
        
        temp = temp_element.get_text(strip=True).replace('현재 온도', '').replace('°', '')
        
        # 2. 날씨 상태 (맑음, 흐림 등)
        desc_element = soup.select_one('.before_slash') or soup.select_one('.cast_txt') or soup.select_one('.weather_before_slash')
        desc = desc_element.get_text(strip=True) if desc_element else "정보 없음"
        
        # 3. 미세먼지 정보
        dust_elements = soup.select('.today_chart_list .txt')
        pm10 = dust_elements[0].get_text(strip=True) if len(dust_elements) > 0 else "보통"
        pm25 = dust_elements[1].get_text(strip=True) if len(dust_elements) > 1 else "보통"
        
        # 4. 기온별 옷차림 추천 (자동 로직)
        try:
            t_val = float(temp)
            if t_val >= 28: outfit = "매우 더워요! 반팔, 반바지, 린넨 소재를 추천합니다. ☀️"
            elif t_val >= 23: outfit = "반팔 티셔츠나 얇은 셔츠가 적당한 날씨예요. 👕"
            elif t_val >= 20: outfit = "얇은 가디건이나 긴팔 티셔츠를 준비하세요. 🧥"
            elif t_val >= 17: outfit = "맨투맨이나 청바지 입기 딱 좋은 날씨입니다. 👖"
            elif t_val >= 12: outfit = "자켓이나 셔츠 위에 가디건을 껴입으세요. 🧣"
            elif t_val >= 9: outfit = "트렌치코트나 얇은 패딩이 필요할 수 있어요. 🧥"
            elif t_val >= 5: outfit = "코트나 가죽 자켓 등 두꺼운 외투를 입으세요. 🧤"
            else: outfit = "매우 추워요! 패딩과 목도리를 꼭 챙기세요! ❄️"
        except:
            outfit = "현재 기온에 맞춰 단정한 옷차림을 추천합니다."

        # 답변 구성
        report = f"""
안녕하세요! AI 기상캐스터입니다. 🎤
**{city}**의 실시간 기상 정보입니다!

🌡️ **현재 기온:** {temp}°C ({desc})
😷 **미세먼지:** {pm10} / **초미세먼지:** {pm25}

👗 **오늘의 코디 추천:**
{outfit}

🚀 **외출 팁:**
- 현재 날씨가 {desc} 상태이니 외출 시 참고하세요!
- 미세먼지 수치가 '{pm10}'입니다. 건강 관리에 유의하세요!
        """
        return report
    except Exception as e:
        return f"죄송합니다. 기상 데이터를 가져오는 중 오류가 발생했습니다. (사유: {str(e)})"

# --- 3. 채팅 화면 표시 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. 채팅 입력 및 로직 ---
if prompt := st.chat_input("지역 날씨를 물어보세요 (예: 서울 날씨)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 검색어 최적화
        search_query = prompt if "날씨" in prompt else f"{prompt} 날씨"
        answer = get_weather(search_query)
        
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

# 사이드바
with st.sidebar:
    st.header("⚙️ 관리 메뉴")
    st.subheader("AI 기상캐스터")
    if st.button('🗑️ 대화 기록 삭제'):
        st.session_state.messages = []
        st.rerun()
