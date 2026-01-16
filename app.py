import streamlit as st
import requests
import os
from google import genai
from dotenv import load_dotenv
from datetime import datetime

# 1. Load Keys
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

# --- HELPER: WMO CODE TO EMOJI ---
def get_weather_emoji(code):
    if code == 0: return "☀️"
    if code in [1, 2, 3]: return "⛅"
    if code in [45, 48]: return "🌫️"
    if code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: return "🌧️"
    if code in [71, 73, 75, 77, 85, 86]: return "❄️"
    if code in [95, 96, 99]: return "⛈️"
    return "☁️"

# --- HELPER: VOLUME TRANSLATOR ---
def translate_liters_to_goods(liters):
    if liters <= 0: return "No extra space."
    elif liters < 10: return "🛍️ Fits: Small souvenirs, duty-free snacks."
    elif liters < 25: return "🛍️ Fits: 1 pair of shoes, 2-3 t-shirts, gifts."
    elif liters < 45: return "🛍️ Fits: 2 pairs of shoes, jeans, light jacket."
    elif liters < 70: return "🛍️ Fits: Heavy Winter Coat, boots, 3 pairs of jeans."
    elif liters < 100: return "🛍️ Fits: 2 checked bags worth! A whole new wardrobe + gifts."
    else: return "🛍️ Fits: Massive Haul! Multiple coats, appliances, shoes for the whole family."

# --- WEATHER TOOL (CACHED) ---
@st.cache_data(ttl=3600) 
def get_weather_data(city_name):
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        geo_response = requests.get(geo_url).json()
        if "results" not in geo_response: return None
        
        lat = geo_response["results"][0]["latitude"]
        long = geo_response["results"][0]["longitude"]

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&daily=weather_code,temperature_2m_max,temperature_2m_min&current=temperature_2m,weather_code&temperature_unit=fahrenheit&forecast_days=16"
        return requests.get(weather_url).json()
    except: return None

# --- CAPACITY ENGINE ---
def calculate_capacity_metrics(luggage_counts, duration, shopping_intent, formal_count, walking_level, avg_temp=None):
    CAPACITY_MAP = { "backpack": 20, "carry_on": 40, "checked": 100 }
    total_capacity = (luggage_counts['backpack'] * CAPACITY_MAP['backpack']) + \
                     (luggage_counts['carry_on'] * CAPACITY_MAP['carry_on']) + \
                     (luggage_counts['checked'] * CAPACITY_MAP['checked'])
    
    base_daily_load = 3.5 
    bulk_multiplier = 1.0
    if avg_temp is not None:
        if avg_temp < 50: bulk_multiplier = 1.4
        elif avg_temp > 75: bulk_multiplier = 0.8
    
    daily_load = base_daily_load * bulk_multiplier
    tech_kit = 2.0 
    shoes_vol = 3.0 if walking_level == "High" else 1.5
    formal_vol = 4.0 * formal_count 
    estimated_load = (duration * daily_load) + tech_kit + shoes_vol + formal_vol
    
    SHOPPING_RESERVE = { "None": 0.0, "Light": 0.10, "Medium": 0.20, "Heavy": 0.30 }
    reserved_space = total_capacity * SHOPPING_RESERVE[shopping_intent]
    
    final_used = estimated_load
    usage_pct = (final_used + reserved_space) / total_capacity if total_capacity > 0 else 1.1
    
    return {
        "total_L": total_capacity,
        "used_L": round(final_used, 1),
        "reserved_L": round(reserved_space, 1),
        "usage_pct": min(usage_pct, 1.0),
        "is_overpacked": usage_pct > 1.0,
        "bulk_multiplier": bulk_multiplier
    }

# 3. Logic Helper
def get_trip_context(arrival, depart, shopping_intent, luggage_counts):
    delta = depart - arrival
    duration = max(1, delta.days + 1)
    shopping_note = "Standard packing."
    if shopping_intent == "Heavy":
        if luggage_counts['checked'] > 0: shopping_note = "User plans HEAVY shopping. Suggest packing checked bag only 50% full."
        elif luggage_counts['carry_on'] > 0: shopping_note = "CRITICAL: Heavy shopping with Carry-on. Reduce clothing by 30%."
        else: shopping_note = "CRITICAL: Heavy shopping with Backpack. Minimalist capsule wardrobe only."
    return duration, shopping_note

# 4. AI Generator
def generate_smart_packing_list(city, weather_json, profile_data):
    formal_instruction = "No formal events."
    if profile_data['formal_count'] > 0:
        formal_instruction = f"IMPORTANT: User has {profile_data['formal_count']} formal events. Include exactly {profile_data['formal_count']} formal outfits."

    prompt = f"""
    Act as an Expert Travel Logistics Manager.
    DESTINATION: {city}
    WEATHER: {weather_json.get('daily', 'N/A')}
    TRIP PROFILE: {profile_data}
    CONSTRAINTS: 
    1. {profile_data['shopping_note']}
    2. BREVITY: Keep item descriptions under 10 words. Functional only.
    3. DAILY PLANNER: This must be SHORT and punchy. Maximum 15 words per time block.
    
    OUTPUT FORMAT (Strict Markdown):
    ### 🌤️ Daily Planner
    * **Morning:** [Max 15 words. Specific layering tactic.]
    * **Afternoon:** [Max 15 words. Specific layering tactic.]
    * **Evening:** [Max 15 words. Specific layering tactic.]
    
    ### ✈️ Wear On Plane (Space Savers)
    * **[Item 1]:** [Brief reason]
    * **[Item 2]:** [Brief reason]
    
    ### 🎒 The Packing List
    | Category | Item | Qty | Notes |
    | :--- | :--- | :--- | :--- |
    | Tops | ... | ... | ... |
    """
    response = client.models.generate_content(model="gemini-flash-latest", contents=prompt)
    return response.text

# 5. UI Setup
st.set_page_config(page_title="TravelCast AI v5.9", page_icon="🧳", layout="wide") 

# --- CRITICAL CSS FIX FOR MOBILE WHITESPACE ---
st.markdown("""
    <style>
        /* 1. Reduce the crazy default padding on mobile */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 5rem !important;
        }
        /* 2. Force the main app container to fill screen height */
        div[data-testid="stAppViewContainer"] {
            min-height: 100vh;
            overflow-x: hidden;
        }
        /* 3. Fix Horizontal Scrolling for Weather */
        div[data-testid="stMarkdownContainer"] > div {
             overflow-x: auto !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🧳 Luggage Optimizer")
st.caption("TravelCast AI")

# --- INPUT SECTION ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Trip Details")
    city = st.text_input("Destination", placeholder="e.g. Tokyo")
    arrival_date = st.date_input("Arrival")
    depart_date = st.date_input("Departure")
    purpose = st.multiselect("Purpose", ["Business", "Vacation", "Adventure", "Romantic"])
    
with col2:
    st.subheader("2. Luggage & Load")
    c_lug1, c_lug2, c_lug3 = st.columns(3)
    with c_lug1: backpacks = st.number_input("Backpacks (20L)", 0, 3, 1)
    with c_lug2: carry_ons = st.number_input("Carry-ons (40L)", 0, 3, 0)
    with c_lug3: checked = st.number_input("Checked (100L)", 0, 3, 0)
    
    shopping = st.select_slider("Shopping Intent", ["None", "Light", "Medium", "Heavy"])
    is_formal = st.checkbox("Formal Events?")
    formal_count = st.number_input("Count", 1, 10, 1) if is_formal else 0
    walking = st.select_slider("Walking", ["Low", "Medium", "High"])

# --- REAL-TIME CALCULATOR ---
luggage_counts = {"backpack": backpacks, "carry_on": carry_ons, "checked": checked}
metrics = None
avg_temp_preview = None

if city:
    weather_preview = get_weather_data(city)
    if weather_preview and 'current' in weather_preview:
        avg_temp_preview = weather_preview['current']['temperature_2m']

if arrival_date and depart_date:
    dur = max(1, (depart_date - arrival_date).days + 1)
    metrics = calculate_capacity_metrics(luggage_counts, dur, shopping, formal_count, walking, avg_temp=avg_temp_preview)
    
    if not metrics['is_overpacked']:
        st.divider()
        pct_used = (metrics['used_L'] / metrics['total_L']) * 100
        pct_reserved = (metrics['reserved_L'] / metrics['total_L']) * 100
        pct_free = 100 - pct_used - pct_reserved
        total_potential = round((metrics['total_L'] - metrics['used_L']) + metrics['reserved_L'], 1)
        
        st.markdown("### ✅ Ready to Pack!")
        weather_note = " • ❄️ Winter Bulk" if metrics['bulk_multiplier'] > 1.0 else " • ☀️ Summer Light" if metrics['bulk_multiplier'] < 1.0 else ""
        st.caption(f"Estimated {int(pct_free)}% Free Space{weather_note}")

        st.markdown(f"""
        <div style="display: flex; width: 100%; height: 50px; border-radius: 12px; overflow: hidden; margin-bottom: 12px; border: 1px solid #ddd;">
            <div style="width: {pct_used}%; background-color: #7f8c8d;"></div>
            <div style="width: {pct_reserved}%; background-color: #9b59b6;"></div>
            <div style="width: {pct_free}%; background-color: #2ecc71;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container(border=True):
            st.markdown(f"**🛍️ Total Shopping Potential: {total_potential} Liters**")
            if total_potential > 60:
                 st.warning("⚠️ **Checked Bag Warning:** Watch your weight limit (50lb/23kg).")

# --- GENERATE BUTTON ---
if st.button("Generate Optimized List", type="primary"):
    if not city:
        st.error("Please enter a city.")
    else:
        with st.spinner("Analyzing weather satellites..."):
            weather_data = get_weather_data(city)
            if weather_data and "daily" in weather_data:
                st.divider()
                st.subheader(f"🌤️ Weather: {city}")
                
                # --- HORIZONTAL WEATHER STRIP ---
                daily = weather_data['daily']
                weather_html = """
                <div style="display: flex; overflow-x: auto; gap: 12px; padding-bottom: 10px; margin-bottom: 20px; white-space: nowrap; -webkit-overflow-scrolling: touch;">
                """
                for i in range(min(7, len(daily['time']))):
                    day = datetime.strptime(daily['time'][i], "%Y-%m-%d").strftime("%b %d")
                    emoji = get_weather_emoji(daily['weather_code'][i])
                    high = round(daily['temperature_2m_max'][i])
                    low = round(daily['temperature_2m_min'][i])
                    weather_html += f"""
                    <div style="min-width: 80px; text-align: center; border: 1px solid #444; border-radius: 10px; padding: 10px; background-color: rgba(255,255,255,0.05); display: inline-block;">
                        <div style="font-weight: bold; font-size: 14px;">{day}</div>
                        <div style="font-size: 24px;">{emoji}</div>
                        <div style="font-size: 12px; opacity: 0.8;">{high}°/{low}°</div>
                    </div>"""
                weather_html += "</div>"
                
                # RENDER WITH HTML ALLOWED
                st.markdown(weather_html, unsafe_allow_html=True)
                
                _, shop_note = get_trip_context(arrival_date, depart_date, shopping, luggage_counts)
                payload = { "duration": dur, "purpose": purpose, "formal_count": formal_count, "luggage_counts": luggage_counts, "shopping_note": shop_note, "gender": "User", "walking": walking }
                
                res = generate_smart_packing_list(city, weather_data, payload)
                
                if "### 💡 Pro Tip" in res:
                    main, tip = res.split("### 💡 Pro Tip")
                    st.markdown(main)
                    st.divider()
                    with st.expander("💡 **Insider Pro Tip**"):
                        st.markdown(tip)
                else:
                    st.markdown(res)
            else:
                st.error("City not found.")