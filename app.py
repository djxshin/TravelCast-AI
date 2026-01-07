import streamlit as st
import requests
import os
from google import genai
from dotenv import load_dotenv
from datetime import datetime

# 1. Load Keys & Configure Client
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Initialize the new Client (as you had it before)
client = genai.Client(api_key=api_key)

# 2. Weather Tool (KEPT from your previous version)
def get_weather_data(city_name):
    try:
        # Geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        geo_response = requests.get(geo_url).json()
        if "results" not in geo_response:
            return None
        
        latitude = geo_response["results"][0]["latitude"]
        longitude = geo_response["results"][0]["longitude"]

        # Weather Fetching
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,precipitation,weather_code,wind_speed_10m&wind_speed_unit=mph&temperature_unit=fahrenheit"
        weather_response = requests.get(weather_url).json()
        return weather_response

    except Exception as e:
        return {"error": str(e)}

# 3. The New Logic Helper (Calculates Days & Shopping Constraints)
def get_trip_context(arrival, depart, shopping_intent, luggage_type):
    # Calculate Duration
    delta = depart - arrival
    duration = max(1, delta.days + 1)
    
    # Calculate Shopping Constraint
    shopping_note = "Standard packing."
    if shopping_intent == "Heavy":
        if luggage_type == "Carry-on Only":
            shopping_note = "CRITICAL: User plans HEAVY shopping. Reduce clothing count by 30% to leave empty space in carry-on."
        elif luggage_type == "Backpack Only":
            shopping_note = "CRITICAL: User plans HEAVY shopping in a BACKPACK. Suggest minimalist capsule wardrobe only."
            
    return duration, shopping_note

# 4. The AI Generator (Now combines Weather + Profile)
def generate_smart_packing_list(city, weather_json, profile_data):
    
    prompt = f"""
    Act as a professional travel stylist. Create a smart packing list for this trip.
    
    DESTINATION: {city}
    REAL-TIME WEATHER DATA: {weather_json}
    
    TRIP PROFILE:
    - Traveler: {profile_data['gender']}, Age {profile_data['age']}
    - Duration: {profile_data['duration']} Days
    - Purpose: {profile_data['purpose']}
    - Formal Events: {'Yes' if profile_data['formal'] else 'No'}
    - Activity Level: {profile_data['walking']} walking
    - Luggage: {profile_data['luggage']}
    
    CONSTRAINT: {profile_data['shopping_note']}
    
    INSTRUCTIONS:
    1. Analyze the Weather Data: Give a 1-sentence "Feels Like" summary.
    2. Create the Packing List: Calculate exact quantities for {profile_data['duration']} days.
    3. Custom Logic:
       - If {profile_data['walking']} is 'High', prioritize specific footwear.
       - If 'Formal' is true, add a separate 'Formal Event' section.
       - If Shopping is 'Heavy', strictly follow the constraint to reduce item count.
    
    Output in clean Markdown.
    """
    
    response = client.models.generate_content(
        model="gemini-flash-latest", # Or "gemini-flash-latest" depending on access
        contents=prompt
    )
    return response.text

# 5. The UI (Expanded with your New Features)
st.set_page_config(page_title="TravelCast AI", page_icon="✈️")
st.title("✈️ TravelCast AI v2.0")
st.caption("Live Weather + Smart Packing Logic")

# --- INPUT SECTION ---
with st.container():
    st.subheader("1. Trip Details")
    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("Destination City", placeholder="e.g. Tokyo")
        gender = st.selectbox("Gender", ["Male", "Female", "Non-Binary"])
        age_group = st.selectbox("Age Group", ["18-30", "30-45", "45-70"])
    with col2:
        arrival_date = st.date_input("Arrival")
        depart_date = st.date_input("Departure")

    st.subheader("2. Logistics & Style")
    purpose = st.selectbox("Trip Purpose", ["Business", "Vacation", "Adventure/Hiking", "Mixed"])
    
    col3, col4 = st.columns(2)
    with col3:
        walking_level = st.select_slider("Walking Amount", options=["Low", "Medium", "High"])
        is_formal = st.checkbox("Formal Events?")
    with col4:
        luggage_type = st.radio("Luggage", ["Backpack Only", "Carry-on Only", "Checked Bag"])
        shopping_intent = st.select_slider("Shopping Intent", options=["None", "Light", "Heavy"])

# --- GENERATION SECTION ---
if st.button("Generate Smart List"):
    if not city:
        st.error("Please enter a city!")
    elif arrival_date > depart_date:
        st.error("Arrival date must be before Departure date.")
    else:
        with st.spinner(f"Contacting Weather Satellites & AI Stylist for {city}..."):
            
            # 1. Get Real Weather
            weather_data = get_weather_data(city)
            
            if weather_data and "error" not in weather_data:
                # 2. Process Logic
                duration, shopping_note = get_trip_context(arrival_date, depart_date, shopping_intent, luggage_type)
                
                profile_payload = {
                    "gender": gender,
                    "age": age_group,
                    "duration": duration,
                    "purpose": purpose,
                    "walking": walking_level,
                    "formal": is_formal,
                    "luggage": luggage_type,
                    "shopping_note": shopping_note
                }
                
                # 3. Call AI
                try:
                    result = generate_smart_packing_list(city, weather_data, profile_payload)
                    st.success("Packing List Generated!")
                    st.markdown(result)
                    
                    with st.expander("Debug Data"):
                        st.write("Weather:", weather_data)
                        st.write("Profile:", profile_payload)
                        
                except Exception as e:
                    st.error(f"AI Error: {e}")
            else:
                st.error("Could not find weather data for that city.")