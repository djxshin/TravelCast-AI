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
    # --- 1. PATH SETUP ---
    # We are in /views, we need to go up one level to root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    
    # HARD CODED: ONLY look for the clean image
    img_path = os.path.join(root_dir, "splash_bg_clean.jpg")

    # --- 2. DEBUG & LOAD ---
    if not os.path.exists(img_path):
        st.error(f"CRITICAL ERROR: Could not find image at: {img_path}")
        st.stop()
    
    bin_str = get_base64(img_path)
    bg_css = f'background-image: url("data:image/jpeg;base64,{bin_str}");'

    # --- 3. CSS ---
    st.markdown(f"""
    <style>
    .stApp {{
        {bg_css}
        background-size: cover;
        background-position: center bottom; /* Anchors image to bottom */
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    header, footer {{ display: none !important; }}
    
    /* PUSH CONTENT TO BOTTOM */
    .block-container {{
        height: 90vh !important;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        padding-bottom: 3rem !important;
    }}

    /* FROSTED GLASS BUTTONS */
    div[data-testid="stButton"] > button {{
        background-color: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;
        border-radius: 30px;
        padding: 15px 25px;
        font-size: 18px;
        font-weight: 600;
        width: 100%;
        transition: transform 0.2s;
    }}
    
    div[data-testid="stButton"] > button:hover {{
        background-color: rgba(255, 255, 255, 0.25);
        transform: scale(1.02);
        border-color: white;
    }}
    </style>
    """, unsafe_allow_html=True)

    # --- 4. BUTTONS ---
    c1, c2, c3 = st.columns([1, 1, 1.2])
    
    with c1: 
        st.button("Log In", use_container_width=True)
            
    with c2: 
        st.button("Sign Up", use_container_width=True)
            
    with c3:
        if st.button("Guest Mode ✈️", type="primary", use_container_width=True):
            st.session_state['page'] = 'main'
            st.rerun()