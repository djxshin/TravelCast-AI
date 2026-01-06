import streamlit as st
import requests
import os
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# 2. Define the "Tool" Function (The Logic)
def get_weather_data(city_name):
    """
    Takes a city name, finds its coordinates, and fetches current weather.
    """
    try:
        # Step A: Find the coordinates (Geocoding)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        geo_response = requests.get(geo_url).json()

        if "results" not in geo_response:
            return None # City not found

        latitude = geo_response["results"][0]["latitude"]
        longitude = geo_response["results"][0]["longitude"]

        # Step B: Get the actual weather (Forecasting)
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,precipitation,weather_code&wind_speed_unit=mph&temperature_unit=fahrenheit"
        weather_response = requests.get(weather_url).json()

        return weather_response

    except Exception as e:
        return {"error": str(e)}

# 3. The UI (The Frontend)
st.set_page_config(page_title="TravelCast AI", page_icon="✈️")
st.title("✈️ TravelCast AI")
st.caption("Your AI Travel Assistant powered by Gemini & Open-Meteo")

# Input box for user
city = st.text_input("Where are you traveling?", placeholder="e.g. Tokyo, Paris, New York")

if city:
    with st.spinner(f"Flying to {city}..."):
        # Call our new tool
        weather_data = get_weather_data(city)

        if weather_data:
            # Show the raw data (just to prove it works!)
            st.success("Data received!")
            st.json(weather_data)
        else:
            st.error("City not found. Please try again.")