import streamlit as st
import os
from dotenv import load_dotenv

# 1. Load the secret keys from the .env file
load_dotenv()

# 2. specific setup for the page
st.set_page_config(page_title="TravelCast AI", page_icon="✈️")

# 3. Check if the key works
api_key = os.getenv("GOOGLE_API_KEY")

st.title("✈️ TravelCast Setup Check")

if api_key:
    st.success(f"✅ API Key found! It starts with: {api_key[:4]}...")
else:
    st.error("❌ No API Key found. Check your .env file.")