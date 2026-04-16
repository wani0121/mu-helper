import streamlit as st
import google.generativeai as genai
import requests
from datetime import datetime

# --- 1. 설정 및 Gemini 연결 ---
try:
    # 지완님이 이미 설정해두신 GEMINI_API_KEY를 그대로 사용합니다.
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("Secrets에 'GEMINI_API_KEY'가 설정되어 있는지 확인해주세요.")

# --- 2. 날씨 데이터 수집 함수 (무료 오픈소스 wttr.in 활용) ---
def get_raw_weather(city_name):
    try:
        # 영문 도시명 매핑 (데이터 정확도를 위해)
        city_map = {"성남": "Seongnam", "판교": "Pangyo", "서울": "Seoul", "분당": "Bundang"}
        clean_name = city_name.replace("날씨", "").replace("미세먼지", "").strip()
        eng_city = city_map.get(clean_query := clean_name, clean_name)

        # 날씨와 공기질 데이터를 JSON으로 가져옵니다.
        url = f"https://wttr.in/{eng_city}?format=j1"
        res = requests.get(url, timeout=10)
        return res.json(), clean_query
    except:
        return None, city_name

# --- 3. 페이지 설정 ---
st.set_page_config(page_title="AI 기상캐스터", page_icon="🌤️")
st.title("🌤️ AI 기상캐스터")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. 채팅 화면 표시 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. 대화 로직 ---
if prompt := st.chat_input("지역명을 입력하세요 (예: 성남 날씨, 판교 미세먼지)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # 1. 날씨 데이터 가져오기
        raw_data, target_city = get_raw_weather(prompt)
        
        if raw_data:
            current = raw_data['current_condition'][0]
            # AI에게 줄 요약 데이터 생성
            weather_context = {
                "지역": target_city,
                "온도": current['temp_C'],
                "상태": current['weatherDesc'][0]['value'],
                "습도": current['humidity'],
                "가시거리(미세먼지판단)": current['visibility'],
                "예보": [f"{w['date']}: {w['mintemp_C']}~{w['maxtemp_C']}도" for w in raw_data['weather'][:3]]
            }
        else:
            weather_context = "날씨 데이터를 불러오지 못했습니다. 일반적인 지식으로 답해주세요."

        # 2. Gemini AI에게 브리핑 요청
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            full_prompt = f"""
            너는 전문 'AI 기상캐스터'야. 아래 데이터를 바탕으로 기상 브리핑을 해줘.
            
            [기상 데이터]: {weather_context}
            
            [지침]
            1. 말투: 생동감 있고 친절한 기상캐스터 말투 (이모티콘 ☀️☁️ 적극 사용).
            2. 구성: 현재 기온/상태 -> 미세먼지(가시거리 기반으로 유추) -> 3일 예보 -> 옷차림 추천 순서.
            3. 옷차림 추천: 기온에 맞춰서 아주 구체적으로(예: 가디건, 얇은 니트 등) 추천해줘.
            4. 사용자가 '판교 미세먼지'처럼 물으면 그 부분에 집중해서 답해줘.
            
            [사용자 질문]: {prompt}
            """
            
            response = model.generate_content(full_prompt)
            ai_answer = response.text
            
            message_placeholder.markdown(ai_answer)
            st.session_state.messages.append({"role": "assistant", "content": ai_answer})
            
        except Exception as e:
            st.error(f"AI 답변 생성 중 오류가 발생했습니다: {str(e)}")

# 사이드바
with st.sidebar:
    st.header("⚙️ 서비스 상태")
    st.success("Gemini 1.5 Flash 엔진 가동 중")
    if st.button('🗑️ 대화 기록 삭제'):
        st.session_state.messages = []
        st.rerun()
