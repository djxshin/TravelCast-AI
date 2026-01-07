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

# 2. Weather Tool
def get_weather_data(city_name):
    try:
        # Geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        geo_response = requests.get(geo_url).json()
        if "results" not in geo_response:
            return None
        
        latitude = geo_response["results"][0]["latitude"]
        longitude = geo_response["results"][0]["longitude"]

        # Fetch Daily Highs/Lows
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&current=temperature_2m,weather_code&temperature_unit=fahrenheit"
        weather_response = requests.get(weather_url).json()
        return weather_response

    except Exception as e:
        return {"error": str(e)}

# 3. The Logic Helper
def get_trip_context(arrival, depart, shopping_intent, luggage_counts):
    # Duration
    delta = depart - arrival
    duration = max(1, delta.days + 1)
    
    # Shopping Logic
    shopping_note = "Standard packing."
    
    if shopping_intent == "Heavy":
        if luggage_counts['checked'] > 0:
             shopping_note = "User plans HEAVY shopping but has checked bags. Suggest packing the checked bag only 50% full."
        elif luggage_counts['carry_on'] > 0:
            shopping_note = "CRITICAL: Heavy shopping with only Carry-on. Reduce clothing by 30% and maximize 'Wear on Plane' items."
        else:
            shopping_note = "CRITICAL: Heavy shopping with Backpack only. Suggest minimalist capsule wardrobe."

    return duration, shopping_note

# 4. The AI Generator
def generate_smart_packing_list(city, weather_json, profile_data):
    
    # Dynamic Formal Instruction
    formal_instruction = "No formal events."
    if profile_data['formal_count'] > 0:
        formal_instruction = f"IMPORTANT: User has {profile_data['formal_count']} specific formal events (e.g. dinners/galas). You MUST include exactly {profile_data['formal_count']} formal outfit sets (Suit/Dress/Shoes) in the list."

    prompt = f"""
    Act as an elite Travel Stylist. Generate a cleaner, highly organized packing list.

    DESTINATION: {city}
    WEATHER DATA (Daily Max/Min): {weather_json.get('daily', 'N/A')}
    CURRENT CONDITIONS: {weather_json.get('current', 'N/A')}
    
    TRIP PROFILE:
    - Traveler: {profile_data['gender']}, Age {profile_data['age']}
    - Duration: {profile_data['duration']} Days
    - Purpose: {', '.join(profile_data['purpose'])}
    - Activity Level: {profile_data['walking']} walking
    - LUGGAGE: {profile_data['luggage_counts']}
    
    CONSTRAINTS: 
    1. {profile_data['shopping_note']}
    2. SPACE SAVER RULE: Identify the bulkies items (Heavy Jackets, Boots, Hoodies). You MUST tell the user to WEAR these on the plane.
    3. {formal_instruction}
    
    OUTPUT FORMAT (Strict Markdown):
    
    ### 🌤️ Weather & Vibe
    [General 1-sentence summary of the city's current vibe]
    * **Morning:** [Temp/Feel] - [Specific advice: e.g. "Crisp cold, need thermal layers"]
    * **Afternoon:** [Temp/Feel] - [Specific advice: e.g. "Warms up, shed the heavy coat"]
    * **Evening:** [Temp/Feel] - [Specific advice: e.g. "Drops freezing, add scarf/gloves"]

    ### ✈️ Wear On Plane (Space Saver Mode)
    * List the bulkiest items here to save bag space.
    
    ### 🎒 The Packing List
    | Category | Item | Qty | Fabric/Style Note |
    | :--- | :--- | :--- | :--- |
    | Tops | ... | ... | ... |
    | Bottoms | ... | ... | ... |
    | Formal Wear | ... | ... | ... |
    | Shoes | ... | ... | ... |
    | Essentials | ... | ... | ... |

    ### 💡 Smart Tips
    * [Tip about shopping/luggage management]
    * [Tip about local style/walking]
    """
    
    response = client.models.generate_content(
        model="gemini-flash-latest", 
        contents=prompt
    )
    return response.text

# 5. The Updated UI
st.set_page_config(page_title="TravelCast AI v3.0", page_icon="✈️", layout="wide") 
st.title("✈️ TravelCast AI v3.0")
st.markdown("### Smart Packing Assistant")

# --- INPUT SECTION ---
with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Who & Where")
        city = st.text_input("Destination City", placeholder="e.g. New York, London")
        col_demo_1, col_demo_2 = st.columns(2)
        with col_demo_1:
            gender = st.selectbox("Gender", ["Male", "Female", "Non-Binary"])
        with col_demo_2:
            age_group = st.selectbox("Age Group", ["18-30", "30-45", "45-70"])
            
        arrival_date = st.date_input("Arrival Date")
        depart_date = st.date_input("Departure Date")

    with col2:
        st.subheader("2. Trip Details")
        purpose = st.multiselect("Trip Purpose (Select all that apply)", 
                                 ["Business", "Vacation", "Adventure/Hiking", "Romantic", "Family Visit"])
        
        walking_level = st.select_slider("Daily Walking", options=["Low", "Medium", "High"])
        
        # --- NEW FORMAL EVENT LOGIC ---
        is_formal = st.checkbox("Formal Events (Dinners/Galas)?")
        formal_count = 0
        if is_formal:
            formal_count = st.number_input("How many Formal Events?", min_value=1, max_value=10, value=1)
        
        st.divider()
        
        st.subheader("3. Luggage & Shopping")
        col_lug_1, col_lug_2, col_lug_3 = st.columns(3)
        with col_lug_1:
            backpacks = st.number_input("Backpacks", 0, 3, 1)
        with col_lug_2:
            carry_ons = st.number_input("Carry-ons", 0, 3, 0)
        with col_lug_3:
            checked_bags = st.number_input("Checked Bags", 0, 3, 0)
            
        shopping_intent = st.select_slider("Shopping Intent", options=["None", "Light", "Medium", "Heavy"])

# --- GENERATION SECTION ---
if st.button("Generate Smart List", type="primary"):
    if not city:
        st.error("Please enter a destination city.")
    elif arrival_date > depart_date:
        st.error("Arrival date must be before Departure date.")
    elif not purpose:
         st.error("Please select at least one trip purpose.")
    else:
        with st.spinner(f"Analyzing weather patterns for {city} & optimizing luggage space..."):
            
            # 1. Get Data
            weather_data = get_weather_data(city)
            
            if weather_data and "error" not in weather_data:
                # 2. Process Logic
                luggage_counts = {"backpack": backpacks, "carry_on": carry_ons, "checked": checked_bags}
                duration, shopping_note = get_trip_context(arrival_date, depart_date, shopping_intent, luggage_counts)
                
                profile_payload = {
                    "gender": gender,
                    "age": age_group,
                    "duration": duration,
                    "purpose": purpose,
                    "walking": walking_level,
                    "formal_count": formal_count, # Sending the specific number
                    "luggage_counts": luggage_counts,
                    "shopping_note": shopping_note
                }
                
                # 3. Call AI
                try:
                    result = generate_smart_packing_list(city, weather_data, profile_payload)
                    st.success(f"Packing List Ready for {duration}-Day Trip!")
                    st.markdown(result)
                    
                except Exception as e:
                    st.error(f"AI Error: {e}")
            else:
                st.error("Could not find weather data. Please check the city name.")