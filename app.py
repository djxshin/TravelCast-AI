import streamlit as st
from views.splash import show_splash
from views.luggage import show_luggage_page

# --- GLOBAL CONFIG ---
st.set_page_config(page_title="TravelCast AI", page_icon="🧳", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'splash'

# --- PAGE ROUTER ---
if st.session_state['page'] == 'splash':
    show_splash()

elif st.session_state['page'] == 'main':
    show_luggage_page()

    # FORCE UPDATE: 2.1