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

# --- NEW: CAPACITY ENGINE ---
def calculate_capacity_metrics(luggage_counts, duration, shopping_intent, formal_count, walking_level):
    # A. Define Capacities (in Liters)
    CAPACITY_MAP = {
        "backpack": 20,
        "carry_on": 40,
        "checked": 100
    }
    
    total_capacity = (luggage_counts['backpack'] * CAPACITY_MAP['backpack']) + \
                     (luggage_counts['carry_on'] * CAPACITY_MAP['carry_on']) + \
                     (luggage_counts['checked'] * CAPACITY_MAP['checked'])
    
    # B. Define Consumption (in Liters)
    # Base load per day (Clothes + Toiletries)
    daily_load = 3.5 
    
    # Fixed loads
    tech_kit = 2.0 
    shoes_vol = 3.0 if walking_level == "High" else 1.5
    formal_vol = 4.0 * formal_count # Suits are bulky
    
    estimated_load = (duration * daily_load) + tech_kit + shoes_vol + formal_vol
    
    # C. Shopping Reserve
    SHOPPING_RESERVE = {
        "None": 0.0,
        "Light": 0.10,   # Reserve 10%
        "Medium": 0.20,  # Reserve 20%
        "Heavy": 0.30    # Reserve 30%
    }
    reserve_pct = SHOPPING_RESERVE[shopping_intent]
    reserved_space = total_capacity * reserve_pct
    
    # D. Final Metrics
    final_used = estimated_load
    remaining_space = total_capacity - final_used - reserved_space
    
    usage_pct = (final_used + reserved_space) / total_capacity if total_capacity > 0 else 1.1
    
    return {
        "total_L": total_capacity,
        "used_L": round(final_used, 1),
        "reserved_L": round(reserved_space, 1),
        "usage_pct": min(usage_pct, 1.0),
        "is_overpacked": usage_pct > 1.0
    }

# 2. Weather Tool
def get_weather_data(city_name):
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        geo_response = requests.get(geo_url).json()
        if "results" not in geo_response: return None
        
        lat = geo_response["results"][0]["latitude"]
        long = geo_response["results"][0]["longitude"]

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&current=temperature_2m,weather_code&temperature_unit=fahrenheit"
        return requests.get(weather_url).json()
    except: return None

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

# 4. AI Generator
def generate_smart_packing_list(city, weather_json, profile_data):
    formal_instruction = "No formal events."
    if profile_data['formal_count'] > 0:
        formal_instruction = f"IMPORTANT: User has {profile_data['formal_count']} formal events. Include exactly {profile_data['formal_count']} formal outfits."

    prompt = f"""
    Act as an elite Travel Stylist. 
    
    DESTINATION: {city}
    WEATHER: {weather_json.get('daily', 'N/A')}
    TRIP PROFILE: {profile_data}
    
    CONSTRAINTS: 
    1. {profile_data['shopping_note']}
    2. SPACE SAVER: Identify bulky items (Coats, Boots) to WEAR ON PLANE.
    3. {formal_instruction}
    
    OUTPUT FORMAT (Strict Markdown):
    
    ### 🌤️ Trip Forecast
    [Brief specific weather advice for Morning/Afternoon/Evening]

    ### ✈️ Wear On Plane (Space Saver)
    * List heavy items here.
    
    ### 🎒 The Packing List
    | Category | Item | Qty | Notes |
    | :--- | :--- | :--- | :--- |
    | Tops | ... | ... | ... |
    | Bottoms | ... | ... | ... |
    | Shoes | ... | ... | ... |
    
    ### 💡 Pro Tip
    * [One specific tip based on destination]
    """
    
    response = client.models.generate_content(model="gemini-flash-latest", contents=prompt)
    return response.text

# 5. UI Setup
st.set_page_config(page_title="TravelCast AI v4.0", page_icon="🧳", layout="wide") 
st.title("🧳 Luggage Optimizer (TravelCast AI)")
st.caption("Capacity Calculation + AI Styling")

# --- INPUT SECTION ---
with st.container():
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
# We calculate this BEFORE the button press to give instant feedback
luggage_counts = {"backpack": backpacks, "carry_on": carry_ons, "checked": checked}
if arrival_date and depart_date:
    dur = max(1, (depart_date - arrival_date).days + 1)
    
    # Run the Math
    metrics = calculate_capacity_metrics(luggage_counts, dur, shopping, formal_count, walking)
    
    st.divider()
    st.subheader("📊 Luggage Capacity Analysis")
    
    # Display the Progress Bar
    bar_color = "red" if metrics['is_overpacked'] else "green"
    st.progress(metrics['usage_pct'])
    
    # Display the Data
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("Total Capacity", f"{metrics['total_L']} Liters")
    with m_col2:
        st.metric("Est. Clothing Load", f"{metrics['used_L']} Liters")
    with m_col3:
        st.metric("Reserved for Shopping", f"{metrics['reserved_L']} Liters")

    if metrics['is_overpacked']:
        st.error(f"⚠️ OVERPACKED! You are trying to fit {metrics['used_L'] + metrics['reserved_L']}L into a {metrics['total_L']}L container. Add a bag or cut the shopping.")
    else:
        st.success(f"✅ Safe! You have {round(metrics['total_L'] - metrics['used_L'] - metrics['reserved_L'], 1)}L of free space remaining.")

# --- GENERATE BUTTON ---
if st.button("Generate Optimized List", type="primary"):
    if metrics['is_overpacked']:
        st.warning("Proceeding, but the AI will have to cut items aggressively to fit.")
        
    with st.spinner("Optimizing wardrobe..."):
        weather_data = get_weather_data(city)
        if weather_data:
            _, shop_note = get_trip_context(arrival_date, depart_date, shopping, luggage_counts)
            
            payload = {
                "duration": dur,
                "purpose": purpose,
                "formal_count": formal_count,
                "luggage_counts": luggage_counts,
                "shopping_note": shop_note,
                "gender": "User", "age": "Adult", "walking": walking # Simplified for demo
            }
            
            res = generate_smart_packing_list(city, weather_data, payload)
            st.markdown(res)
        else:
            st.error("City not found.")