import streamlit as st
import requests
import os
import base64
from google import genai
from dotenv import load_dotenv
from datetime import datetime

# --- 1. CONFIG & SESSION SETUP ---
st.set_page_config(page_title="TravelCast AI", page_icon="🧳", layout="wide")

if 'page' not in st.session_state:
    st.session_state['page'] = 'splash'

# --- 2. HELPER FUNCTIONS ---
def get_weather_emoji(code):
    if code == 0: return "☀️"
    if code in [1, 2, 3]: return "⛅"
    if code in [45, 48]: return "🌫️"
    if code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: return "🌧️"
    if code in [71, 73, 75, 77, 85, 86]: return "❄️"
    if code in [95, 96, 99]: return "⛈️"
    return "☁️"

def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

# --- NEW: STEP 1 - SEARCH CITIES ---
@st.cache_data(ttl=3600)
def search_city_options(query):
    """Searches for cities and returns a list of detailed location options."""
    if not query or len(query) < 2: return []
    try:
        # Request 5 options so user can choose
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=5&language=en&format=json"
        geo_response = requests.get(geo_url).json()
        
        if "results" not in geo_response: return []
        
        options = []
        for res in geo_response["results"]:
            # Create a clean label: "Paris, Texas, United States"
            city = res.get('name')
            region = res.get('admin1', '')
            country = res.get('country', '')
            
            # Smart formatting to avoid double commas
            label_parts = [city]
            if region and region != city: label_parts.append(region)
            if country: label_parts.append(country)
            
            options.append({
                "label": ", ".join(label_parts),
                "lat": res["latitude"],
                "long": res["longitude"],
                "country": country,
                "city": city
            })
        return options
    except: return []

# --- NEW: STEP 2 - GET WEATHER BY COORDS ---
@st.cache_data(ttl=3600)
def get_weather_data(lat, long):
    """Fetches weather using specific coordinates from the selected city."""
    try:
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&daily=weather_code,temperature_2m_max,temperature_2m_min&current=temperature_2m,weather_code&temperature_unit=fahrenheit&forecast_days=16"
        return requests.get(weather_url).json()
    except: return None

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
        "total_L": total_capacity, "used_L": round(final_used, 1),
        "reserved_L": round(reserved_space, 1), 
        "usage_pct": min(usage_pct, 1.0),
        "is_overpacked": usage_pct > 1.0, 
        "bulk_multiplier": bulk_multiplier
    }

def get_trip_context(arrival, depart, shopping_intent, luggage_counts):
    delta = depart - arrival
    duration = max(1, delta.days + 1)
    shopping_note = "Standard packing."
    if shopping_intent == "Heavy":
        if luggage_counts['checked'] > 0: shopping_note = "User plans HEAVY shopping. Suggest packing checked bag only 50% full."
        elif luggage_counts['carry_on'] > 0: shopping_note = "CRITICAL: Heavy shopping with Carry-on. Reduce clothing by 30%."
        else: shopping_note = "CRITICAL: Heavy shopping with Backpack. Minimalist capsule wardrobe only."
    return duration, shopping_note

def generate_smart_packing_list(city_label, weather_json, profile_data, client):
    if not client: return "Error: Google API Key not found."

    formal_instruction = "No formal events."
    if profile_data.get('formal_count', 0) > 0:
        formal_instruction = f"IMPORTANT: User has {profile_data['formal_count']} formal events. Include exactly {profile_data['formal_count']} formal outfits."

    prompt = f"""
    Act as an Expert Travel Logistics Manager.
    DESTINATION: {city_label}
    WEATHER: {weather_json.get('daily', 'N/A')}
    TRIP PROFILE: {profile_data}
    CONSTRAINTS: 
    1. {profile_data.get('shopping_note', 'Standard packing')}
    2. BREVITY: Keep item descriptions under 10 words. Functional only.
    3. DAILY PLANNER: This must be SHORT and punchy. Maximum 15 words per time block.
    4. PRO TIP: Provide specific advice on managing indoor/outdoor temperature transitions (e.g., the 'Subway Peel' strategy).
    5. {formal_instruction}
    
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
    
    ### 💡 Pro Tip
    [Write a detailed, strategic tip here.]
    """
    
    response = client.models.generate_content(model="gemini-flash-latest", contents=prompt)
    return response.text

# --- 3. PAGE ROUTING ---

if st.session_state['page'] == 'splash':
    img_path = "splash_bg.png"
    if os.path.exists(img_path):
        bin_str = get_base64(img_path)
        bg_css = f'background-image: url("data:image/png;base64,{bin_str}");'
    else:
        bg_css = 'background-color: #1e1e1e;'

    st.markdown(f"""
    <style>
    .stApp {{ {bg_css} background-size: cover; background-position: center; }}
    .stApp::before {{ content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.3); z-index: -1; }}
    header, footer {{ display: none; }}
    .block-container {{ padding-top: 35vh !important; text-align: center; }}
    .hero-title {{ font-size: 3.5rem; font-weight: 700; color: white; text-shadow: 0px 2px 4px rgba(0,0,0,0.6); margin-bottom: 3rem; }}
    div[data-testid="stButton"] > button {{ background-color: rgba(30,30,30,0.8); color: white; border: 1px solid rgba(255,255,255,0.3); width: 100%; }}
    div[data-testid="stColumn"]:nth-child(3) button {{ background-color: #FF4B4B; border: none; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='hero-title'>Want a getaway?<br>Let's pack!</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1.2])
    with c1: st.button("Log In")
    with c2: st.button("Sign Up")
    with c3:
        if st.button("Guest Mode ✈️"):
            st.session_state['page'] = 'main'
            st.rerun()

elif st.session_state['page'] == 'main':
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key) if api_key else None

    # CSS for horizontal scroll
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
        
        # --- NEW: SEARCH BAR + CONFIRMATION DROPDOWN ---
        search_query = st.text_input("Destination", placeholder="Type city (e.g. Paris)")
        
        selected_location_data = None
        
        if search_query:
            # Step 1: Search for matches
            options = search_city_options(search_query)
            
            if options:
                # Step 2: Show dropdown
                # We map the label back to the data object using an index or dictionary lookup
                labels = [opt["label"] for opt in options]
                choice = st.selectbox("📍 Confirm Location", labels)
                
                # Find the data for the chosen label
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

    # METRICS & DISPLAY
    luggage_counts = {"backpack": backpacks, "carry_on": carry_ons, "checked": checked}
    if arrival_date and depart_date:
        dur = max(1, (depart_date - arrival_date).days + 1)
        
        # --- LOGIC UPDATE: Use selected location data if available ---
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

    # GENERATE BUTTON
    if st.button("Generate Optimized List", type="primary"):
        if not selected_location_data or not api_key:
            st.error("Please select a valid location from the dropdown and check your API Key.")
        else:
            with st.spinner("Analyzing weather satellites..."):
                # Use the PRECISE weather data we already fetched
                weather_data = weather_preview
                
                # --- WEATHER DISPLAY ---
                if weather_data and "daily" in weather_data:
                    st.divider()
                    
                    # Display the FULL label (e.g. "Paris, Texas, United States")
                    st.subheader(f"🌤️ Weather: {selected_location_data['label']}")
                    
                    daily = weather_data['daily']
                    cards_html = ""
                    for i in range(min(7, len(daily['time']))):
                        day = datetime.strptime(daily['time'][i], "%Y-%m-%d").strftime("%b %d")
                        emoji = get_weather_emoji(daily['weather_code'][i])
                        high = round(daily['temperature_2m_max'][i])
                        low = round(daily['temperature_2m_min'][i])
                        
                        # NO INDENTATION in this string to avoid code-block rendering
                        cards_html += f'<div style="min-width: 85px; text-align: center; border: 1px solid #444; border-radius: 10px; padding: 10px; background-color: rgba(255,255,255,0.05);"><div style="font-weight: bold; font-size: 14px; margin-bottom: 5px;">{day}</div><div style="font-size: 28px; margin-bottom: 5px;">{emoji}</div><div style="font-size: 12px; opacity: 0.8;">{high}° / {low}°</div></div>'

                    final_html = f'<div class="weather-scroll-container">{cards_html}</div>'
                    st.markdown(final_html, unsafe_allow_html=True)

                # --- AI GENERATION ---
                _, shop_note = get_trip_context(arrival_date, depart_date, shopping, luggage_counts)
                payload = { 
                    "duration": dur, 
                    "purpose": purpose, 
                    "formal_count": formal_count, 
                    "luggage_counts": luggage_counts, 
                    "shopping_note": shop_note, 
                    "gender": "User", 
                    "walking": walking 
                }
                
                try:
                    # Pass the detailed label to the AI so it knows context
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