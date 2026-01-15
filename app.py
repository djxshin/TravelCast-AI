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
    if liters <= 0:
        return "No extra space."
    elif liters < 10:
        return "🛍️ Fits: Small souvenirs, duty-free snacks."
    elif liters < 25:
        return "🛍️ Fits: 1 pair of shoes, 2-3 t-shirts, gifts."
    elif liters < 45:
        return "🛍️ Fits: 2 pairs of shoes, jeans, light jacket."
    elif liters < 70:
        return "🛍️ Fits: Heavy Winter Coat, boots, 3 pairs of jeans."
    elif liters < 100:
        return "🛍️ Fits: 2 checked bags worth! A whole new wardrobe + gifts."
    else:
        return "🛍️ Fits: Massive Haul! Multiple coats, appliances, shoes for the whole family."

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
    # A. Define Capacities
    CAPACITY_MAP = { "backpack": 20, "carry_on": 40, "checked": 100 }
    
    total_capacity = (luggage_counts['backpack'] * CAPACITY_MAP['backpack']) + \
                     (luggage_counts['carry_on'] * CAPACITY_MAP['carry_on']) + \
                     (luggage_counts['checked'] * CAPACITY_MAP['checked'])
    
    # B. Define Consumption (Dynamic)
    base_daily_load = 3.5 
    
    # Temperature Factor
    bulk_multiplier = 1.0
    if avg_temp is not None:
        if avg_temp < 50: # Cold: Heavy knits/jackets
            bulk_multiplier = 1.4
        elif avg_temp > 75: # Hot: Light fabrics
            bulk_multiplier = 0.8
    
    daily_load = base_daily_load * bulk_multiplier
    
    # Fixed loads
    tech_kit = 2.0 
    shoes_vol = 3.0 if walking_level == "High" else 1.5
    formal_vol = 4.0 * formal_count 
    
    estimated_load = (duration * daily_load) + tech_kit + shoes_vol + formal_vol
    
    # C. Shopping Reserve
    SHOPPING_RESERVE = { "None": 0.0, "Light": 0.10, "Medium": 0.20, "Heavy": 0.30 }
    reserve_pct = SHOPPING_RESERVE[shopping_intent]
    reserved_space = total_capacity * reserve_pct
    
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
        if luggage_counts['checked'] > 0:
             shopping_note = "User plans HEAVY shopping. Suggest packing checked bag only 50% full."
        elif luggage_counts['carry_on'] > 0:
            shopping_note = "CRITICAL: Heavy shopping with Carry-on. Reduce clothing by 30%."
        else:
            shopping_note = "CRITICAL: Heavy shopping with Backpack. Minimalist capsule wardrobe only."

    return duration, shopping_note

# 4. AI Generator (Updated for Conciseness & Structure)
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
    4. NO FLUFF: Do not describe colors or vibes.
    
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
    | Bottoms | ... | ... | ... |
    | Shoes | ... | ... | ... |

    ### 💡 Pro Tip
    [Write a detailed, high-value strategic tip here. This is the "If you know you know" section.]
    """
    
    response = client.models.generate_content(model="gemini-flash-latest", contents=prompt)
    return response.text

# 5. UI Setup
st.set_page_config(page_title="TravelCast AI v5.8", page_icon="🧳", layout="wide") 
st.title("🧳 Luggage Optimizer (TravelCast AI)")
st.caption("Capacity Calculation + AI Styling")

# --- INPUT SECTION (Simplified Layout for Mobile) ---
# Removed the outer st.container() to reduce layout thrashing on mobile keyboards
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
    
    # --- SILENT HEADER (Only show positive, hide error) ---
    if not metrics['is_overpacked']:
        st.divider()
        # Calculate percentages
        pct_used = (metrics['used_L'] / metrics['total_L']) * 100
        pct_reserved = (metrics['reserved_L'] / metrics['total_L']) * 100
        pct_free = 100 - pct_used - pct_reserved
        
        physical_free = round(metrics['total_L'] - metrics['used_L'], 1)
        total_potential = round(physical_free + metrics['reserved_L'], 1)
        
        # --- NEW CLEANER HEADER ---
        st.markdown("### ✅ Ready to Pack!")
        
        # Small Caption for context
        weather_note = ""
        if metrics['bulk_multiplier'] > 1.0: weather_note = " • ❄️ Winter Bulk Detected"
        elif metrics['bulk_multiplier'] < 1.0: weather_note = " • ☀️ Summer Light Load"
        
        st.caption(f"Estimated {int(pct_free)}% Free Space{weather_note}")

        # --- THE BIGGER VISUAL BAR (50px) ---
        st.markdown(f"""
        <div style="display: flex; width: 100%; height: 50px; border-radius: 12px; overflow: hidden; margin-bottom: 12px; border: 1px solid #ddd; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="width: {pct_used}%; background-color: #7f8c8d;"></div>
            <div style="width: {pct_reserved}%; background-color: #9b59b6;"></div>
            <div style="width: {pct_free}%; background-color: #2ecc71;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- THE LEGEND ---
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; font-family: sans-serif; font-size: 13px; color: #666; margin-bottom: 25px;">
            <div style="display: flex; align-items: center;">
                <span style="color: #7f8c8d; font-size: 16px; line-height: 0;">●</span>&nbsp;<span>Clothes</span>
            </div>
            <div style="display: flex; align-items: center;">
                <span style="color: #9b59b6; font-size: 16px; line-height: 0;">●</span>&nbsp;<span>Shopping</span>
            </div>
            <div style="display: flex; align-items: center;">
                <span style="color: #2ecc71; font-size: 16px; line-height: 0;">●</span>&nbsp;<span>Free Space</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- THE SUMMARY CARD ---
        with st.container(border=True):
            st.markdown("**🛍️ Total Shopping Potential**")
            st.markdown(f"<h1 style='margin: 0; font-size: 32px;'>{total_potential} Liters</h1>", unsafe_allow_html=True)
            st.caption(f"_{translate_liters_to_goods(total_potential)}_")
            
            if total_potential > 60:
                 st.warning("⚠️ **Checked Bag Warning:** Filling this entire volume will likely exceed the 50lb (23kg) weight limit. Please weigh your bag before heading to the airport.")

# --- GENERATE BUTTON ---
if st.button("Generate Optimized List", type="primary"):
    if not city:
        st.error("Please enter a city.")
    else:
        if metrics and metrics['is_overpacked']:
             st.error(f"⚠️ **OVERPACKED!** You need {metrics['used_L'] + metrics['reserved_L']}L but only have {metrics['total_L']}L. Proceeding, but the AI will cut items aggressively.")
            
        with st.spinner("Analyzing weather satellites & optimizing wardrobe..."):
            weather_data = get_weather_data(city)
            
            if weather_data and "daily" in weather_data:
                st.divider()
                st.subheader(f"🌤️ Weather Forecast: {city}")
                
                # --- NEW HORIZONTAL SCROLL WEATHER STRIP ---
                daily_data = weather_data['daily']
                dates = daily_data['time']
                codes = daily_data['weather_code']
                max_temps = daily_data['temperature_2m_max']
                min_temps = daily_data['temperature_2m_min']
                
                # Build HTML string for horizontal scroll
                weather_html = """
                <div style="display: flex; overflow-x: auto; gap: 12px; padding-bottom: 10px; margin-bottom: 20px; white-space: nowrap; -webkit-overflow-scrolling: touch;">
                """
                
                for i in range(min(7, len(dates))):
                    day_date = datetime.strptime(dates[i], "%Y-%m-%d").strftime("%b %d")
                    emoji = get_weather_emoji(codes[i])
                    high = round(max_temps[i])
                    low = round(min_temps[i])
                    
                    weather_html += f"""
                    <div style="min-width: 85px; text-align: center; border: 1px solid #444; border-radius: 10px; padding: 10px; background-color: rgba(255,255,255,0.05); display: inline-block;">
                        <div style="font-weight: bold; font-size: 14px; margin-bottom: 5px;">{day_date}</div>
                        <div style="font-size: 28px; margin-bottom: 5px;">{emoji}</div>
                        <div style="font-size: 12px; opacity: 0.8;">{high}° / {low}°</div>
                    </div>
                    """
                
                weather_html += "</div>"
                # This is the critical line that must be on the server to fix the HTML issue
                st.markdown(weather_html, unsafe_allow_html=True)
                
                # 2. Get Context & Generate AI
                _, shop_note = get_trip_context(arrival_date, depart_date, shopping, luggage_counts)
                
                payload = {
                    "duration": dur,
                    "purpose": purpose,
                    "formal_count": formal_count,
                    "luggage_counts": luggage_counts,
                    "shopping_note": shop_note,
                    "gender": "User", "age": "Adult", "walking": walking
                }
                
                full_response = generate_smart_packing_list(city, weather_data, payload)
                
                # 3. Split Response
                if "### 💡 Pro Tip" in full_response:
                    main_content, pro_tip_content = full_response.split("### 💡 Pro Tip")
                    st.markdown(main_content)
                    st.divider()
                    with st.expander("💡 **Insider Pro Tip (Tap to Unlock)**"):
                        st.markdown(pro_tip_content.strip())
                else:
                    st.markdown(full_response)
                    
            else:
                st.error("Could not retrieve weather data. City might be spelled incorrectly.")