import streamlit as st
import os
from google import genai
from dotenv import load_dotenv
from datetime import datetime

# --- IMPORT THE NEW UTILS ---
from utils.weather import get_weather_emoji, search_city_options, get_weather_data
from utils.logic import calculate_capacity_metrics, get_trip_context
from utils.ai import generate_smart_packing_list

# --- MAIN PAGE VIEW ---
def show_luggage_page():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key) if api_key else None

    st.markdown("""
        <style>
        .weather-scroll-container {
            display: flex;
            overflow-x: auto;
            gap: 12px;
            padding-bottom: 10px;
            margin-bottom: 20px;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🧳 Luggage Optimizer")
    st.caption("TravelCast AI")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Trip Details")
        search_query = st.text_input("Destination", placeholder="Type city (e.g. Paris)")
        selected_location_data = None
        
        if search_query:
            options = search_city_options(search_query)
            if options:
                labels = [opt["label"] for opt in options]
                choice = st.selectbox("📍 Confirm Location", labels)
                for opt in options:
                    if opt["label"] == choice:
                        selected_location_data = opt
                        break
            else:
                st.warning("City not found. Try adding the country code.")

        arrival_date = st.date_input("Arrival")
        depart_date = st.date_input("Departure")
        purpose = st.multiselect("Purpose", ["Business", "Vacation", "Adventure", "Romantic"])
    
    with col2:
        st.subheader("2. Luggage & Load")
        c1, c2, c3 = st.columns(3)
        with c1: backpacks = st.number_input("Backpacks (20L)", 0, 3, 1)
        with c2: carry_ons = st.number_input("Carry-ons (40L)", 0, 3, 0)
        with c3: checked = st.number_input("Checked (100L)", 0, 3, 0)
        shopping = st.select_slider("Shopping Intent", ["None", "Light", "Medium", "Heavy"])
        is_formal = st.checkbox("Formal Events?")
        formal_count = st.number_input("Count", 1, 10, 1) if is_formal else 0
        walking = st.select_slider("Walking", ["Low", "Medium", "High"])

    luggage_counts = {"backpack": backpacks, "carry_on": carry_ons, "checked": checked}
    if arrival_date and depart_date:
        dur = max(1, (depart_date - arrival_date).days + 1)
        weather_preview = None
        avg_temp = None
        if selected_location_data:
            weather_preview = get_weather_data(selected_location_data['lat'], selected_location_data['long'])
            if weather_preview and 'current' in weather_preview:
                avg_temp = weather_preview['current']['temperature_2m']
        
        metrics = calculate_capacity_metrics(luggage_counts, dur, shopping, formal_count, walking, avg_temp)
        
        if not metrics['is_overpacked']:
            st.divider()
            pct_used = (metrics['used_L'] / metrics['total_L']) * 100
            pct_reserved = (metrics['reserved_L'] / metrics['total_L']) * 100
            pct_free = 100 - pct_used - pct_reserved
            total_potential = round((metrics['total_L'] - metrics['used_L']) + metrics['reserved_L'], 1)
            
            st.markdown("### ✅ Ready to Pack!")
            bar_html = f'<div style="display: flex; width: 100%; height: 30px; border-radius: 5px; overflow: hidden; margin-bottom: 10px; border: 1px solid #555;"><div style="width: {pct_used}%; background-color: #7f8c8d;"></div><div style="width: {pct_reserved}%; background-color: #9b59b6;"></div><div style="width: {pct_free}%; background-color: #2ecc71;"></div></div>'
            st.markdown(bar_html, unsafe_allow_html=True)
            st.markdown(f"**🛍️ Total Shopping Potential: {total_potential} Liters**")
            if total_potential > 60:
                 st.warning("⚠️ **Checked Bag Warning:** Watch your weight limit (50lb/23kg).")

    if st.button("Generate Optimized List", type="primary"):
        if not selected_location_data or not api_key:
            st.error("Please select a valid location from the dropdown and check your API Key.")
        else:
            with st.spinner("Analyzing weather satellites..."):
                weather_data = weather_preview
                if weather_data and "daily" in weather_data:
                    st.divider()
                    st.subheader(f"🌤️ Weather: {selected_location_data['label']}")
                    daily = weather_data['daily']
                    cards_html = ""
                    for i in range(min(7, len(daily['time']))):
                        day = datetime.strptime(daily['time'][i], "%Y-%m-%d").strftime("%b %d")
                        emoji = get_weather_emoji(daily['weather_code'][i])
                        high = round(daily['temperature_2m_max'][i])
                        low = round(daily['temperature_2m_min'][i])
                        cards_html += f'<div style="min-width: 85px; text-align: center; border: 1px solid #444; border-radius: 10px; padding: 10px; background-color: rgba(255,255,255,0.05);"><div style="font-weight: bold; font-size: 14px; margin-bottom: 5px;">{day}</div><div style="font-size: 28px; margin-bottom: 5px;">{emoji}</div><div style="font-size: 12px; opacity: 0.8;">{high}° / {low}°</div></div>'
                    final_html = f'<div class="weather-scroll-container">{cards_html}</div>'
                    st.markdown(final_html, unsafe_allow_html=True)

                _, shop_note = get_trip_context(arrival_date, depart_date, shopping, luggage_counts)
                payload = { 
                    "duration": dur, "purpose": purpose, "formal_count": formal_count, 
                    "luggage_counts": luggage_counts, "shopping_note": shop_note, 
                    "gender": "User", "walking": walking 
                }
                try:
                    res = generate_smart_packing_list(selected_location_data['label'], weather_data, payload, client)
                    if "### 💡 Pro Tip" in res:
                        main, tip = res.split("### 💡 Pro Tip")
                        st.markdown(main)
                        st.divider()
                        with st.expander("💡 **Insider Pro Tip**"):
                            st.markdown(tip)
                    else:
                        st.markdown(res)
                except Exception as e:
                    st.error(f"Error: {str(e)}")