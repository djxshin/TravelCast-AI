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
    # --- VISUAL CHECK ---
    # If you don't see this text, the server code IS NOT UPDATED.
    st.markdown("<h3 style='text-align: center; color: white; position: absolute; top: 10px; width: 100%; z-index: 999;'>VERSION 2.0 - CLEAN LAYOUT</h3>", unsafe_allow_html=True)

    # --- PATH FINDER ---
    # Try finding the file in the current working directory (Root) first
    img_filename = "splash_bg_clean.jpg"
    
    # Check 1: Root Folder
    if os.path.exists(img_filename):
        img_path = img_filename
    else:
        # Check 2: Relative to this script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        img_path = os.path.join(root_dir, img_filename)

    # --- IMAGE LOADER ---
    if os.path.exists(img_path):
        bin_str = get_base64(img_path)
        bg_css = f'background-image: url("data:image/jpeg;base64,{bin_str}");'
    else:
        # CRITICAL FAIL: Show red screen if image is missing from server
        bg_css = 'background-color: #880000;'
        st.error(f"❌ CRITICAL: '{img_filename}' NOT FOUND on server. Please run: git add {img_filename}")
        st.stop()

    # --- CSS ---
    st.markdown(f"""
    <style>
    .stApp {{
        {bg_css}
        background-size: cover;
        background-position: center bottom;
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

    /* NEW BUTTON STYLE */
    div[data-testid="stButton"] > button {{
        background-color: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;
        border-radius: 30px;
        padding: 15px 0px;
        font-size: 18px;
        font-weight: 600;
        width: 100%;
    }}
    
    div[data-testid="stButton"] > button:hover {{
        background-color: rgba(255, 255, 255, 0.3);
        transform: scale(1.02);
        border-color: white;
    }}
    </style>
    """, unsafe_allow_html=True)

    # --- BUTTONS ---
    c1, c2, c3 = st.columns([1, 1, 1.2])
    
    with c1: 
        st.button("Log In", use_container_width=True)
            
    with c2: 
        st.button("Sign Up", use_container_width=True)
            
    with c3:
        if st.button("Guest Mode ✈️", type="primary", use_container_width=True):
            st.session_state['page'] = 'main'
            st.rerun()