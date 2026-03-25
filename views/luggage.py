import streamlit as st
import os
from google import genai
from dotenv import load_dotenv
from datetime import datetime, timedelta

from utils.weather import get_weather_emoji, search_city_options, get_weather_data
from utils.logic import calculate_capacity_metrics, get_trip_context
from utils.ai import generate_smart_packing_list

def show_luggage_page():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key) if api_key else None

    st.markdown("<style>.weather-scroll-container { display: flex; overflow-x: auto; gap: 12px; padding-bottom: 10px; margin-bottom: 20px; -webkit-overflow-scrolling: touch; scrollbar-width: none; }</style>", unsafe_allow_html=True)

    st.title("🧳 Luggage Optimizer")
    st.caption("TravelCast AI")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Trip Details")
        search_query = st.text_input("Destination", placeholder="Type city...")
        selected_location_data = None
        if search_query:
            options = search_city_options(search_query)
            if options:
                choice = st.selectbox("📍 Confirm Location", [opt["label"] for opt in options])
                selected_location_data = next(opt for opt in options if opt["label"] == choice)

        today = datetime.now().date()
        arrival_date = st.date_input("Arrival", value=today + timedelta(days=1), min_value=today)
        depart_date = st.date_input("Departure", value=arrival_date + timedelta(days=7), min_value=arrival_date)
        purpose = st.multiselect("Purpose", ["Business", "Vacation", "Adventure", "Romantic"])
    
    with col2:
        st.subheader("2. Luggage & Load")
        c1, c2, c3 = st.columns(3)
        with c1: backpacks = st.number_input("Backpacks", 0, 3, 1)
        with c2: carry_ons = st.number_input("Carry-ons", 0, 3, 0)
        with c3: checked = st.number_input("Checked", 0, 3, 0)
        shopping = st.select_slider("Shopping Intent", ["None", "Light", "Medium", "Heavy"])
        is_formal = st.checkbox("Formal Events?")
        formal_count = st.number_input("Count", 1, 10, 1) if is_formal else 0
        walking = st.select_slider("Walking", ["Low", "Medium", "High"])

    if arrival_date and depart_date:
        dur = max(1, (depart_date - arrival_date).days + 1)
        weather_preview, avg_temp = None, 65 
        
        if selected_location_data:
            weather_preview = get_weather_data(selected_location_data['lat'], selected_location_data['long'], arrival_date.strftime("%Y-%m-%d"), dur)
            if weather_preview and 'current' in weather_preview:
                avg_temp = weather_preview['current']['temperature_2m']
        
        metrics = calculate_capacity_metrics({"backpack": backpacks, "carry_on": carry_ons, "checked": checked}, dur, shopping, formal_count, walking, avg_temp)
        
        st.divider()
        st.markdown("### 🧳 Luggage Capacity")
        
        # UI IMPROVEMENT: Turn meter Red if overpacked instead of hiding it
        is_over = metrics.get('is_overpacked', False)
        c_used = "#e74c3c" if is_over else "#7f8c8d" # Red if over
        
        pct_used = (metrics['used_L'] / metrics['total_L']) * 100
        pct_res = (metrics['reserved_L'] / metrics['total_L']) * 100
        pct_free = max(0, 100 - pct_used - pct_res)

        bar_html = f'<div style="display: flex; width: 100%; height: 30px; border-radius: 5px; overflow: hidden; margin-bottom: 8px; border: 1px solid #555;"><div style="width: {pct_used}%; background-color: {c_used};"></div><div style="width: {pct_res}%; background-color: #9b59b6;"></div><div style="width: {pct_free}%; background-color: #2ecc71;"></div></div>'
        legend_html = f'<div style="display: flex; justify-content: space-between; font-size: 14px; color: #ddd; margin-bottom: 20px;"><div><span style="color:{c_used};">■</span> Essentials ({int(pct_used)}%)</div><div><span style="color:#9b59b6;">■</span> Reserved ({int(pct_res)}%)</div><div><span style="color:#2ecc71;">■</span> Free ({int(pct_free)}%)</div></div>'
        st.markdown(bar_html + legend_html, unsafe_allow_html=True)
        
        if is_over: st.error("⚠️ **Overcapacity!** You need more luggage or fewer items.")

    if st.button("Generate Optimized List", type="primary"):
        if not selected_location_data or not api_key:
            st.error("Select destination and check API Key.")
        else:
            with st.spinner("Analyzing..."):
                if weather_preview and "daily" in weather_preview:
                    st.divider()
                    st.subheader(f"🌤️ Weather: {selected_location_data['label']} ({weather_preview.get('forecast_type')})")
                    daily, cards_html = weather_preview['daily'], ""
                    for i in range(len(daily['time'])):
                        if daily['temperature_2m_max'][i] is None: continue
                        day = datetime.strptime(daily['time'][i], "%Y-%m-%d").strftime("%b %d")
                        emoji = get_weather_emoji(daily['weather_code'][i])
                        cards_html += f'<div style="min-width: 85px; text-align: center; border: 1px solid #444; border-radius: 10px; padding: 10px; background-color: rgba(255,255,255,0.05);"><b>{day}</b><br><span style="font-size: 24px;">{emoji}</span><br>{round(daily["temperature_2m_max"][i])}°</div>'
                    st.markdown(f'<div class="weather-scroll-container">{cards_html}</div>', unsafe_allow_html=True)
                else:
                    st.warning("🌤️ Weather data currently unavailable for these dates. AI will use seasonal averages.")

                _, shop_note = get_trip_context(arrival_date, depart_date, shopping, {"backpack": backpacks, "carry_on": carry_ons, "checked": checked})
                payload = { "duration": dur, "purpose": purpose, "formal_count": formal_count, "luggage_counts": {"backpack": backpacks, "carry_on": carry_ons, "checked": checked}, "shopping_note": shop_note, "gender": "User", "walking": walking }
                st.markdown(generate_smart_packing_list(selected_location_data['label'], weather_preview, payload, client))