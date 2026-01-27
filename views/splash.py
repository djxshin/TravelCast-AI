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
    
    # Check Root then Relative
    if os.path.exists(img_filename):
        img_path = img_filename
    else:
        img_path = os.path.join(root_dir, img_filename)

    # --- IMAGE LOADER ---
    if os.path.exists(img_path):
        bin_str = get_base64(img_path)
        bg_css = f'background-image: url("data:image/jpeg;base64,{bin_str}");'
    else:
        bg_css = 'background-color: #0e0e0e;'

    # --- CSS CONFIGURATION ---
    st.markdown(f"""
    <style>
    /* MAIN BACKGROUND */
    .stApp {{
        {bg_css}
        background-size: contain; /* CRITICAL FIX: Ensures entire image fits */
        background-position: center center; /* Center the image */
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-color: #0e0e0e; /* Matches the dark photo edges */
    }}
    
    /* HIDE DEFAULT ELEMENTS */
    header, footer {{ display: none !important; }}
    
    /* CONTENT CONTAINER - Pushes buttons to bottom */
    .block-container {{
        height: 100vh !important;
        display: flex;
        flex-direction: column;
        justify-content: flex-end; /* Align content to the bottom */
        padding-bottom: 5vh !important; /* Space from bottom edge */
        max-width: 900px; /* Prevent buttons from getting too wide on huge screens */
        margin: 0 auto; /* Center the container */
    }}

    /* BUTTON STYLING */
    div[data-testid="stButton"] > button {{
        background-color: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
        border-radius: 12px;
        padding: 15px 0px;
        font-size: 16px;
        font-weight: 500;
        width: 100%;
        transition: all 0.2s ease-in-out;
    }}
    
    div[data-testid="stButton"] > button:hover {{
        background-color: rgba(255, 255, 255, 0.25);
        border-color: white;
        transform: scale(1.02);
    }}
    </style>
    """, unsafe_allow_html=True)

    # --- BUTTON LAYOUT ---
    # Centered columns with Guest Mode slightly larger
    c1, c2, c3 = st.columns([1, 1, 1.5])
    
    with c1: 
        st.button("Log In", use_container_width=True)
            
    with c2: 
        st.button("Sign Up", use_container_width=True)
            
    with c3:
        # The Primary Action
        if st.button("Guest Mode ✈️", type="primary", use_container_width=True):
            st.session_state['page'] = 'main'
            st.rerun()