import requests
import streamlit as st
from datetime import datetime, timedelta
from collections import Counter

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
    if not query or len(query) < 2: return []
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=5&language=en&format=json"
        geo_response = requests.get(geo_url).json()
        if "results" not in geo_response: return []
        options = []
        for res in geo_response["results"]:
            city, reg, cty = res.get('name'), res.get('admin1', ''), res.get('country', '')
            label = ", ".join(filter(None, [city, reg if reg != city else None, cty]))
            options.append({"label": label, "lat": res["latitude"], "long": res["longitude"], "city": city})
        return options
    except: return []

@st.cache_data(ttl=3600)
def get_weather_data(lat, long, arrival_date_str=None, trip_duration=7):
    try:
        today = datetime.now().date()
        arrival_date = datetime.strptime(arrival_date_str, "%Y-%m-%d").date() if arrival_date_str else today
        end_date = arrival_date + timedelta(days=min(trip_duration - 1, 13))
        
        # SMART FIX: Check if the END of the trip is outside the 16-day live window
        needs_historical = (end_date - today).days > 15

        if not needs_historical:
            start_str, end_str = arrival_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&start_date={start_str}&end_date={end_str}&daily=weather_code,temperature_2m_max,temperature_2m_min&current=temperature_2m,weather_code&temperature_unit=fahrenheit"
            data = requests.get(weather_url).json()
            if "daily" in data:
                data['forecast_type'] = "Live Forecast"
                return data
        
        # Fallback to Historical
        all_max, all_min, all_codes = [], [], []
        for years_back in range(1, 4):
            try: past_start = arrival_date.replace(year=arrival_date.year - years_back)
            except: past_start = arrival_date - timedelta(days=365 * years_back)
            past_end = past_start + timedelta(days=min(trip_duration - 1, 13))
            
            res = requests.get(f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={long}&start_date={past_start.strftime('%Y-%m-%d')}&end_date={past_end.strftime('%Y-%m-%d')}&daily=weather_code,temperature_2m_max,temperature_2m_min&temperature_unit=fahrenheit")
            if res.status_code == 200:
                js = res.json()
                if 'daily' in js:
                    all_max.append(js['daily']['temperature_2m_max'])
                    all_min.append(js['daily']['temperature_2m_min'])
                    all_codes.append(js['daily']['weather_code'])

        if not all_max: return None
        num_days = len(all_max[0])
        avg_max, avg_min, avg_codes = [], [], []
        for d in range(num_days):
            avg_max.append(round(sum(y[d] for y in all_max) / len(all_max), 1))
            avg_min.append(round(sum(y[d] for y in all_min) / len(all_min), 1))
            c_day = [y[d] for y in all_codes]
            mode = Counter(c_day).most_common()
            avg_codes.append(mode[0][0] if mode[0][1] > 1 else 2)

        return {
            "forecast_type": "3-Year Climate Average",
            "daily": {"time": [(arrival_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(num_days)], "temperature_2m_max": avg_max, "temperature_2m_min": avg_min, "weather_code": avg_codes},
            "current": {"temperature_2m": round((avg_max[0] + avg_min[0]) / 2, 1), "weather_code": avg_codes[0]}
        }
    except Exception as e:
        return None