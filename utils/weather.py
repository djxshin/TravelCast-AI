import requests
import streamlit as st
from datetime import datetime, timedelta

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
    """Routes to live forecast OR calculates a 3-year historical average."""
    try:
        today = datetime.now().date()
        needs_historical = False
        arrival_date = None
        
        # 1. Check if we need historical routing
        if arrival_date_str:
            arrival_date = datetime.strptime(arrival_date_str, "%Y-%m-%d").date()
            days_until_trip = (arrival_date - today).days
            if days_until_trip > 14:
                needs_historical = True

        # --- ROUTE A: LIVE FORECAST ---
        if not needs_historical:
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&daily=weather_code,temperature_2m_max,temperature_2m_min&current=temperature_2m,weather_code&temperature_unit=fahrenheit&forecast_days=16"
            data = requests.get(weather_url).json()
            data['forecast_type'] = "Live Forecast"
            return data

        # --- ROUTE B: 3-YEAR HISTORICAL AVERAGE ---
        else:
            all_max_temps = []
            all_min_temps = []
            primary_weather_codes = []
            
            # Loop through the last 3 years
            for years_back in range(1, 4):
                try:
                    past_start = arrival_date.replace(year=arrival_date.year - years_back)
                except ValueError:
                    # Catch Leap Year (Feb 29) error
                    past_start = arrival_date + timedelta(days=-(365 * years_back))
                    
                past_end = past_start + timedelta(days=min(trip_duration, 14))
                
                archive_url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={long}&start_date={past_start.strftime('%Y-%m-%d')}&end_date={past_end.strftime('%Y-%m-%d')}&daily=weather_code,temperature_2m_max,temperature_2m_min&temperature_unit=fahrenheit"
                
                res = requests.get(archive_url)
                if res.status_code == 200:
                    hist_json = res.json()
                    if 'daily' in hist_json:
                        all_max_temps.append(hist_json['daily']['temperature_2m_max'])
                        all_min_temps.append(hist_json['daily']['temperature_2m_min'])
                        primary_weather_codes.append(hist_json['daily']['weather_code'])

            # If we failed to get archive data, fail gracefully
            if not all_max_temps: return None

            # Calculate the averages across the 3 years
            avg_max_temps = []
            avg_min_temps = []
            avg_codes = []
            
            # We assume each year returned the same number of days
            num_days = len(all_max_temps[0])
            for day_idx in range(num_days):
                day_max = sum(year[day_idx] for year in all_max_temps) / len(all_max_temps)
                day_min = sum(year[day_idx] for year in all_min_temps) / len(all_min_temps)
                
                avg_max_temps.append(round(day_max, 1))
                avg_min_temps.append(round(day_min, 1))
                
                # For weather code, just take the most recent year's code for that day to avoid complex mode math
                avg_codes.append(primary_weather_codes[0][day_idx])

            # Construct a fake payload that mimics the Live API structure
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