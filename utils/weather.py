import requests
import streamlit as st

def get_weather_emoji(code):
    if code == 0: return "☀️"
    if code in [1, 2, 3]: return "⛅"
    if code in [45, 48]: return "🌫️"
    if code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: return "🌧️"
    if code in [71, 73, 75, 77, 85, 86]: return "❄️"
    if code in [95, 96, 99]: return "⛈️"
    return "☁️"

@st.cache_data(ttl=3600)
def search_city_options(query):
    """Searches for cities and returns detailed location options."""
    if not query or len(query) < 2: return []
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=5&language=en&format=json"
        geo_response = requests.get(geo_url).json()
        if "results" not in geo_response: return []
        
        options = []
        for res in geo_response["results"]:
            city = res.get('name')
            region = res.get('admin1', '')
            country = res.get('country', '')
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

@st.cache_data(ttl=3600)
def get_weather_data(lat, long):
    """Fetches weather using specific coordinates."""
    try:
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&daily=weather_code,temperature_2m_max,temperature_2m_min&current=temperature_2m,weather_code&temperature_unit=fahrenheit&forecast_days=16"
        return requests.get(weather_url).json()
    except: return None