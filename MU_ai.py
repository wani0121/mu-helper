import streamlit as st
import google.generativeai as genai
import requests

# --- 1. 설정 및 Gemini 연결 ---
api_key = st.secrets.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# --- 2. 안전한 날씨 데이터 수집 함수 (이용량 무제한) ---
def get_safe_weather(city_name):
    try:
        city_map = {"성남": "Seongnam", "판교": "Pangyo", "서울": "Seoul", "분당": "Bundang"}
        clean_name = city_name.replace("날씨", "").replace("미세먼지", "").strip()
        eng_city = city_map.get(clean_name, clean_name)

        url = f"https://wttr.in/{eng_city}?format=j1"
        res = requests.get(url, timeout=10)
        data = res.json()
        
        current = data.get('current_condition', [{}])[0]
        weather_list = data.get('weather', [])
        
        forecast_summary = []
        for w in weather_list[:3]:
            date = w.get('date', '날짜미상')
            low = w.get('mintemp_C') or "??"
            high = w.get('maxtemp_C') or "??"
            forecast_summary.append(f"- {date}: {low}°C ~ {high}°C")

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

# --- 3. UI 설정 ---
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
        weather_info, city = get_safe_weather(prompt)
        
        if not weather_info:
            st.error("날씨 데이터를 가져올 수 없습니다.")
        else:
            # 1단계: AI 없이 기본 정보 즉시 출력 (이용량 소모 없음)
            basic_report = f"""
### 📍 {city} 날씨 리포트
- **현재 기온:** {weather_info['현재온도']}°C ({weather_info['날씨상태']})
- **습도:** {weather_info['습도']}% | **가시거리:** {weather_info['가시거리']}km
- **단기 예보:**
{chr(10).join(weather_info['3일예보'])}
            """
            st.markdown(basic_report)
            
            # 2단계: AI 브리핑 시도 (이용량 남아있을 때만)
            if api_key:
                try:
                    # 가용한 모델 중 가장 안정적인 1.5-flash 우선 시도
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    ai_prompt = f"너는 기상캐스터야. 이 데이터를 보고 친절한 코디 추천과 미세먼지 조언을 3줄로 요약해줘: {weather_info}"
                    
                    response = model.generate_content(ai_prompt)
                    st.info(f"🎤 AI 캐스터의 한마디:\n{response.text}")
                    st.session_state.messages.append({"role": "assistant", "content": basic_report + "\n" + response.text})
                except Exception as e:
                    st.warning("⚠️ 현재 AI 이용량이 많아 기본 정보만 제공합니다. (내일 다시 활성화됩니다)")
                    st.session_state.messages.append({"role": "assistant", "content": basic_report})

# 사이드바
with st.sidebar:
    st.header("⚙️ 시스템 상태")
    st.info("기본 날씨: wttr.in (무제한)")
    st.success("AI 엔진: Gemini (일 20회 제한)")
    if st.button('🗑️ 기록 삭제'):
        st.session_state.messages.clear()
        st.rerun()
