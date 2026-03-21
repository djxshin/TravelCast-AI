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
def get_weather_data(lat, long, arrival_date_str=None, trip_duration=7):
    try:
        today = datetime.now().date()
        needs_historical = False
        arrival_date = today

        if arrival_date_str:
            arrival_date = datetime.strptime(arrival_date_str, "%Y-%m-%d").date()
            if (arrival_date - today).days > 14:
                needs_historical = True

        end_date = arrival_date + timedelta(days=min(trip_duration - 1, 13))

        if not needs_historical:
            start_str = arrival_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&start_date={start_str}&end_date={end_str}&daily=weather_code,temperature_2m_max,temperature_2m_min&current=temperature_2m,weather_code&temperature_unit=fahrenheit"
            data = requests.get(weather_url).json()
            data['forecast_type'] = "Live Forecast"
            return data
        else:
            all_max_temps, all_min_temps, primary_weather_codes = [], [], []
            
            for years_back in range(1, 4):
                try: 
                    past_start = arrival_date.replace(year=arrival_date.year - years_back)
                except ValueError: 
                    past_start = arrival_date + timedelta(days=-(365 * years_back))
                
                past_end = past_start + timedelta(days=min(trip_duration - 1, 13))
                archive_url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={long}&start_date={past_start.strftime('%Y-%m-%d')}&end_date={past_end.strftime('%Y-%m-%d')}&daily=weather_code,temperature_2m_max,temperature_2m_min&temperature_unit=fahrenheit"
                
                res = requests.get(archive_url)
                if res.status_code == 200:
                    hist_json = res.json()
                    if 'daily' in hist_json:
                        all_max_temps.append(hist_json['daily']['temperature_2m_max'])
                        all_min_temps.append(hist_json['daily']['temperature_2m_min'])
                        primary_weather_codes.append(hist_json['daily']['weather_code'])

            if not all_max_temps: return None

            num_days = len(all_max_temps[0])
            avg_max_temps, avg_min_temps, avg_codes = [], [], []
            
            for day_idx in range(num_days):
                day_max = sum(year[day_idx] for year in all_max_temps) / len(all_max_temps)
                day_min = sum(year[day_idx] for year in all_min_temps) / len(all_min_temps)
                avg_max_temps.append(round(day_max, 1))
                avg_min_temps.append(round(day_min, 1))
                
                # --- THE FIX: Smart Tie-Breaker ---
                codes_for_this_day = [year[day_idx] for year in primary_weather_codes]
                if not codes_for_this_day:
                    continue
                    
                code_counts = Counter(codes_for_this_day).most_common()
                
                if code_counts[0][1] > 1:
                    avg_codes.append(code_counts[0][0])
                else:
                    avg_codes.append(2) # Safe Partly Cloudy baseline

            mock_data = {
                "forecast_type": "3-Year Climate Average",
                "daily": {
                    "time": [(arrival_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(num_days)],
                    "temperature_2m_max": avg_max_temps,
                    "temperature_2m_min": avg_min_temps,
                    "weather_code": avg_codes
                },
                "current": {
                    "temperature_2m": round((avg_max_temps[0] + avg_min_temps[0]) / 2, 1),
                    "weather_code": avg_codes[0]
                }
            }
            return mock_data

    except Exception as e: 
        print(f"Weather API Error: {e}")
        return None