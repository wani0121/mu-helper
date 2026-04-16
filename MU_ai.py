import streamlit as st
import google.generativeai as genai
import requests

# --- 1. 설정 및 Gemini 연결 ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Secrets에 'GEMINI_API_KEY'를 설정해주세요.")

# --- 2. 안전한 날씨 데이터 수집 함수 ---
def get_safe_weather(city_name):
    try:
        # 지역명 보정
        city_map = {"성남": "Seongnam", "판교": "Pangyo", "서울": "Seoul", "분당": "Bundang"}
        clean_name = city_name.replace("날씨", "").replace("미세먼지", "").strip()
        eng_city = city_map.get(clean_name, clean_name)

        # 데이터 가져오기 (JSON v1 포맷)
        url = f"https://wttr.in/{eng_city}?format=j1"
        res = requests.get(url, timeout=10)
        data = res.json()
        
        # [핵심] KeyError 방지를 위해 .get() 사용
        current = data.get('current_condition', [{}])[0]
        weather_list = data.get('weather', [])
        
        # 3일 예보 데이터 안전하게 추출
        forecast_summary = []
        for w in weather_list[:3]:
            date = w.get('date', '날짜미상')
            # 키값이 없을 경우를 대비해 여러 후보군 확인
            low = w.get('mintemp_C') or w.get('avgtempC') or "??"
            high = w.get('maxtemp_C') or w.get('avgtempC') or "??"
            forecast_summary.append(f"{date}: {low}~{high}도")

        context = {
            "지역": clean_name,
            "현재온도": current.get('temp_C', '??'),
            "날씨상태": current.get('weatherDesc', [{}])[0].get('value', '알 수 없음'),
            "습도": current.get('humidity', '??'),
            "가시거리": current.get('visibility', '10'), # 미세먼지 유추용
            "3일예보": forecast_summary
        }
        return context, clean_name
    except Exception as e:
        return None, city_name

# --- 3. UI 및 대화 처리 ---
st.set_page_config(page_title="AI 기상캐스터", page_icon="🌤️")
st.title("🌤️ AI 기상캐스터")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("지역을 입력하세요 (예: 성남 날씨, 판교 미세먼지)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # 1. 날씨 컨텍스트 확보
        weather_info, city = get_safe_weather(prompt)
        
        # 2. Gemini AI 브리핑 (이용량 넉넉한 1.5-flash)
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            # 미세먼지 예보 로직을 프롬프트에 강화
            ai_prompt = f"""
            너는 전문 AI 기상캐스터야. 아래 정보를 바탕으로 브리핑해줘.
            
            [데이터]: {weather_info}
            
            [미션]
            - 가시거리(Visibility)가 10km 미만이면 미세먼지가 '나쁨'일 가능성이 높다고 안내해줘.
            - 오늘, 내일, 모레 날씨를 아주 친절하게 이모티콘과 함께 설명해.
            - 현재 온도에 딱 맞는 옷차림(예: 얇은 자켓, 면바지 등)을 제안해.
            - 말투는 활기찬 기상캐스터처럼!
            """
            
            response = model.generate_content(ai_prompt)
            final_msg = response.text
            
            message_placeholder.markdown(final_msg)
            st.session_state.messages.append({"role": "assistant", "content": final_msg})
            
        except Exception as ai_err:
            st.error("AI가 잠시 쉬고 있네요. 다시 시도해 주세요!")
