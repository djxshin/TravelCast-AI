import streamlit as st
import requests
import os
from google import genai # <--- The NEW library import
from dotenv import load_dotenv

# 1. Load Keys & Configure the New Client
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# The new "Client" setup
client = genai.Client(api_key=api_key)

# 2. Define the Weather Tool (Same as before)
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

# 3. Define the AI Agent Function (Updated for New Syntax)
def generate_travel_advice(city, weather_json):
    # Prompt Engineering (Same as before)
    prompt = f"""
    You are an expert travel guide. 
    The user is traveling to {city}.
    
    Here is the REAL-TIME weather data for that location:
    {weather_json}
    
    Based on this specific data (temperature, wind, precipitation), provide:
    1. A witty summary of what it feels like outside.
    2. A "Packing List" with 3 specific items they must bring.
    3. A "Don't Do" warning (e.g. "Don't wear suede shoes").
    
    Keep it short, fun, and helpful.
    """
    
    # <--- NEW CODE SYNTAX --->
    response = client.models.generate_content(
        model="gemini-flash-latest", 
        contents=prompt
    )
    return response.text

# 4. The UI (Same as before)
st.set_page_config(page_title="TravelCast AI", page_icon="✈️")
st.title("✈️ TravelCast AI")
st.caption("Live Weather Agents: Powered by Open-Meteo & Gemini")

city = st.text_input("Where are you traveling?", placeholder="e.g. Paris, Tokyo, Austin")

if city:
    with st.spinner(f"Agent is checking the satellites for {city}..."):
        # Step A: Get Data
        raw_weather = get_weather_data(city)
        
        if raw_weather:
            # Step B: AI Analysis
            try:
                advice = generate_travel_advice(city, raw_weather)
                
                # Step C: Display Result
                st.success(f"Report for {city} Ready!")
                st.markdown(advice)
                
                with st.expander("See Raw System Data (Debug Info)"):
                    st.json(raw_weather)
            except Exception as e:
                st.error(f"AI Error: {e}")
        else:
            st.error("Could not find that city. Try again!")