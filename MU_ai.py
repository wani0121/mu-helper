import streamlit as st
import google.generativeai as genai
import requests

# --- 1. 설정 및 Gemini 연결 ---
# API 키가 없어도 앱이 죽지 않도록 설정합니다.
api_key = st.secrets.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ Streamlit Secrets에 'GEMINI_API_KEY'가 설정되지 않았습니다!")

# --- 2. 날씨 데이터 수집 함수 (안정성 최우선) ---
def get_safe_weather(city_name):
    try:
        # 지역명 매핑
        city_map = {"성남": "Seongnam", "판교": "Pangyo", "서울": "Seoul", "분당": "Bundang"}
        clean_name = city_name.replace("날씨", "").replace("미세먼지", "").strip()
        eng_city = city_map.get(clean_name, clean_name)

        # wttr.in 호출
        url = f"https://wttr.in/{eng_city}?format=j1"
        res = requests.get(url, timeout=10)
        data = res.json()
        
        current = data.get('current_condition', [{}])[0]
        weather_list = data.get('weather', [])
        
        # 3일 예보 데이터 안전 추출
        forecast_summary = []
        for w in weather_list[:3]:
            date = w.get('date', '날짜미상')
            low = w.get('mintemp_C') or w.get('avgtempC') or "??"
            high = w.get('maxtemp_C') or w.get('avgtempC') or "??"
            forecast_summary.append(f"{date}: {low}~{high}도")

        context = {
            "지역": clean_name,
            "현재온도": current.get('temp_C', '??'),
            "날씨상태": current.get('weatherDesc', [{}])[0].get('value', '알 수 없음'),
            "습도": current.get('humidity', '??'),
            "가시거리": current.get('visibility', '10'),
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

# --- 4. 사용자 입력 및 답변 ---
if prompt := st.chat_input("지역명을 입력하세요 (예: 성남 날씨)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # 1. 날씨 정보 가져오기
        weather_info, city = get_safe_weather(prompt)
        
        if not weather_info:
            message_placeholder.error("날씨 서버에 접속할 수 없습니다. 잠시 후 다시 시도해 주세요.")
        else:
            # 2. AI 답변 생성 시도
            if not api_key:
                message_placeholder.warning(f"현재 기온은 {weather_info['현재온도']}도입니다. (AI 키 설정 시 더 자세한 브리핑이 가능합니다)")
            else:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    ai_prompt = f"""
                    너는 전문 AI 기상캐스터야. 아래 정보를 바탕으로 브리핑해줘.
                    
                    [데이터]: {weather_info}
                    
                    [미션]
                    - 가시거리가 10km 미만이면 미세먼지 주의를 당부할 것.
                    - 온도에 맞는 구체적인 옷차림(겉옷 유무 등) 제안.
                    - 3일 예보를 포함해 상냥한 말투로 답할 것.
                    """
                    response = model.generate_content(ai_prompt)
                    ai_answer = response.text
                    message_placeholder.markdown(ai_answer)
                    st.session_state.messages.append({"role": "assistant", "content": ai_answer})
                except Exception as e:
                    message_placeholder.error(f"AI 답변 생성 중 오류가 발생했습니다: {str(e)}")

# 사이드바
with st.sidebar:
    st.header("⚙️ 시스템 정보")
    if api_key:
        st.success("✅ AI 엔진 준비 완료")
    else:
        st.error("❌ AI 키 미설정")
    
    if st.button('🗑️ 기록 삭제'):
        st.session_state.messages = []
        st.rerun()
