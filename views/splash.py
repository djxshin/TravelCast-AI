import streamlit as st
import base64
import os

def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

def show_splash():
    # --- 1. Load Background Image ---
    img_path = "splash_bg.png"
    if os.path.exists(img_path):
        bin_str = get_base64(img_path)
        bg_css = f'background-image: url("data:image/png;base64,{bin_str}");'
    else:
        bg_css = 'background-color: #1e1e1e;'

    # --- 2. CSS: Full Screen & Button Positioning ---
    st.markdown(f"""
    <style>
    /* FORCE FULL SCREEN BACKGROUND */
    .stApp {{
        {bg_css}
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* HIDE HEADER/FOOTER */
    header, footer {{ display: none !important; }}
    
    /* PUSH CONTENT TO BOTTOM */
    .block-container {{
        padding-top: 80vh !important;  /* Push buttons down 80% of screen */
        padding-bottom: 5vh !important;
    }}

    /* CUSTOMIZE BUTTONS TO MATCH YOUR DESIGN */
    div[data-testid="stButton"] > button {{
        background-color: rgba(60, 40, 30, 0.85); /* Dark Brown tint to match your image */
        color: white;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 8px;
        height: 50px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
    }}
    
    div[data-testid="stButton"] > button:hover {{
        background-color: rgba(90, 60, 45, 1.0);
        border-color: white;
        transform: scale(1.02);
    }}
    </style>
    """, unsafe_allow_html=True)

    # --- 3. The Buttons ---
    # We use columns to spread them out horizontally like in your design
    c1, c2, c3 = st.columns([1, 1, 1.2])
    
    with c1: 
        if st.button("Log In", use_container_width=True):
            st.toast("Login coming soon!")
            
    with c2: 
        if st.button("Sign Up", use_container_width=True):
            st.toast("Signup coming soon!")
            
    with c3:
        # PRIMARY ACTION
        if st.button("Guest Mode", use_container_width=True):
            st.session_state['page'] = 'main'
            st.rerun()