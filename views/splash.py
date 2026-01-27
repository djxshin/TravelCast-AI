import streamlit as st
import base64
import os

def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception as e:
        return None

def show_splash():
    # --- PATH FINDER ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    img_filename = "splash_bg_clean.jpg"
    
    if os.path.exists(img_filename):
        img_path = img_filename
    else:
        img_path = os.path.join(root_dir, img_filename)

    # --- IMAGE LOADER ---
    if os.path.exists(img_path):
        bin_str = get_base64(img_path)
        # Using specific position to center the 'contain'ed image
        bg_css = f'background-image: url("data:image/jpeg;base64,{bin_str}");'
    else:
        bg_css = 'background-color: #0e0e0e;'

    # --- CSS CONFIGURATION ---
    st.markdown(f"""
    <style>
    /* MAIN BACKGROUND */
    .stApp {{
        {bg_css}
        background-size: contain; /* Keeps image full without cropping */
        background-position: center center; /* Dead center */
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-color: #000000; /* Black borders to match */
    }}
    
    /* HIDE DEFAULT ELEMENTS */
    header, footer {{ display: none !important; }}
    
    /* RESET CONTAINER - Remove padding so spacer works accurately */
    .block-container {{
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        max-width: 100%;
    }}

    /* BUTTON STYLING */
    div[data-testid="stButton"] > button {{
        background-color: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
        border-radius: 8px;
        height: 50px;
        font-size: 16px;
        font-weight: 500;
        width: 100%;
        transition: all 0.2s ease-in-out;
    }}
    
    div[data-testid="stButton"] > button:hover {{
        background-color: rgba(255, 255, 255, 0.2);
        border-color: white;
        transform: scale(1.02);
    }}
    </style>
    """, unsafe_allow_html=True)

    # --- LAYOUT LOGIC ---
    
    # 1. VERTICAL SPACER
    # This invisible block pushes everything else down by 78% of the viewport height.
    # Adjust '78vh' if you want buttons higher or lower.
    st.markdown('<div style="height: 78vh; width: 100%;"></div>', unsafe_allow_html=True)

    # 2. CENTERED BUTTON ROW
    # We use empty columns on the sides to squeeze the buttons into the middle
    # matching the width of the image content usually.
    _, main_col, _ = st.columns([1, 2, 1]) 
    
    with main_col:
        # Nested columns for the 3 buttons
        c1, c2, c3 = st.columns([1, 1, 1.2])
        
        with c1: 
            st.button("Log In", use_container_width=True)
                
        with c2: 
            st.button("Sign Up", use_container_width=True)
                
        with c3:
            if st.button("Guest Mode ✈️", type="primary", use_container_width=True):
                st.session_state['page'] = 'main'
                st.rerun()