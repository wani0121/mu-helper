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

# --- 2. 데이터 수집 함수 (오픈소스 크롤링 - 무제한 무료) ---
def get_weather(city="서울 날씨"):
    try:
        url = f"https://search.naver.com/search.naver?query={city}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 데이터 추출
        temp = soup.select_one('.temperature_text').text.replace('현재 온도', '').strip()
        desc = soup.select_one('.before_slash').text.strip()
        dust = soup.select('.today_chart_list .txt')
        
        pm10 = dust[0].text if len(dust) > 0 else "정보없음"
        pm25 = dust[1].text if len(dust) > 1 else "정보없음"
        
        # 기온별 옷차림 추천 로직 (AI 대신 프로그래밍된 규칙 사용)
        t_val = float(temp.replace('°', ''))
        if t_val >= 28: outfit = "반팔, 반바지, 린넨 소재 옷이 좋아요! ☀️"
        elif t_val >= 23: outfit = "반팔, 얇은 셔츠나 면바지를 추천해요. 👕"
        elif t_val >= 20: outfit = "긴팔 티셔츠나 얇은 가디건이 적당해요. 🧥"
        elif t_val >= 17: outfit = "니트, 맨투맨, 청바지가 딱 좋은 날씨예요. 👖"
        elif t_val >= 12: outfit = "자켓, 가디건, 야상 등을 챙기세요. 🧣"
        elif t_val >= 9: outfit = "트렌치코트나 여러 겹 껴입는 걸 추천해요. 🧥"
        elif t_val >= 5: outfit = "코트나 가죽 자켓을 꺼낼 때가 됐어요. 🧤"
        else: outfit = "패딩이나 두꺼운 코트, 목도리는 필수입니다! ❄️"

        # 답변 구성 (기상캐스터 말투)
        report = f"""
안녕하세요! AI 기상캐스터입니다. 🎤
요청하신 **{city}**의 실시간 기상 정보입니다!

🌡️ **현재 기온:** {temp} ({desc})
😷 **미세먼지:** {pm10} / **초미세먼지:** {pm25}

👗 **오늘의 코디 추천:**
{outfit}

🚀 **외출 팁:**
- 현재 {desc} 상태이니 참고해서 이동하세요!
- 미세먼지가 '{pm10}' 수준입니다. 건강 유의하세요! 
        """
        return report
    except:
        return "죄송합니다. 해당 지역의 날씨 정보를 가져올 수 없습니다. '서울 날씨'처럼 입력해 보세요! 🔍"

# --- 3. 채팅 화면 표시 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. 채팅 입력 및 로직 ---
if prompt := st.chat_input("지역 날씨를 물어보세요 (예: 서울 날씨)"):
    # 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 모델 없이 날씨 정보 바로 출력
    with st.chat_message("assistant"):
        # 입력값에 '날씨'가 없으면 자동으로 붙여서 검색
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
