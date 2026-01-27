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
    # --- 1. ROBUST IMAGE FINDER (Targeting the NEW clean image) ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    
    # Look for the new clean image name specifically
    possible_paths = [
        os.path.join(root_dir, "splash_bg_clean.jpg"),
        os.path.join(current_dir, "splash_bg_clean.jpg"),
        "splash_bg_clean.jpg"
    ]
    
    img_path = None
    for p in possible_paths:
        if os.path.exists(p):
            img_path = p
            break

    if img_path:
        bin_str = get_base64(img_path)
        bg_css = f'background-image: url("data:image/jpeg;base64,{bin_str}");'
    else:
        bg_css = 'background-color: #1e1e1e;'
        st.error(f"Debug: Could not find 'splash_bg_clean.jpg' in {root_dir}")

    # --- 2. NEW CSS: Clean Layout & Modern Buttons ---
    st.markdown(f"""
    <style>
    /* FORCE FULL SCREEN BACKGROUND */
    .stApp {{
        {bg_css}
        background-size: cover; /* Fill screen */
        background-position: center bottom; /* Anchor to bottom so suitcase is visible */
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* HIDE HEADER/FOOTER */
    header, footer {{ display: none !important; }}
    
    /* LAYOUT CONTAINER - Pushes content to bottom */
    .block-container {{
        height: 95vh !important;
        display: flex;
        flex-direction: column;
        justify-content: flex-end; /* Align items to bottom */
        padding-bottom: 5rem !important; /* Space from bottom edge */
    }}

    /* STYLE THE REAL STREAMLIT BUTTONS (Frosted Glass Look) */
    div[data-testid="stButton"] > button {{
        background-color: rgba(255, 255, 255, 0.15); /* Semi-transparent white */
        backdrop-filter: blur(10px); /* Frosted glass effect */
        -webkit-backdrop-filter: blur(10px); /* Safari support */
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;
        border-radius: 30px; /* Nice rounded corners */
        padding: 15px 25px;
        font-size: 18px;
        font-weight: 600;
        letter-spacing: 1px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        width: 100%;
    }}
    
    /* HOVER EFFECT */
    div[data-testid="stButton"] > button:hover {{
        background-color: rgba(255, 255, 255, 0.25);
        border-color: white;
        transform: translateY(-3px); /* Slight lift */
        box-shadow: 0 7px 14px rgba(0,0,0,0.15);
    }}
    </style>
    """, unsafe_allow_html=True)

    # --- 3. The Buttons Layout ---
    # Use columns to spread them nicely at the bottom
    c1, c2, c3 = st.columns([1, 1, 1.2])
    
    with c1: 
        st.button("Log In", key="btn_login", use_container_width=True)
            
    with c2: 
        st.button("Sign Up", key="btn_signup", use_container_width=True)
            
    with c3:
        # PRIMARY ACTION
        if st.button("Guest Mode ✈️", key="btn_guest", use_container_width=True):
            st.session_state['page'] = 'main'
            st.rerun()