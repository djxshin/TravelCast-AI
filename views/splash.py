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
    # --- 1. ROBUST IMAGE FINDER (for new clean image) ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    
    # Look for the new clean image
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

    # --- 2. CSS: Background & Button Styling ---
    st.markdown(f"""
    <style>
    /* FORCE FULL SCREEN BACKGROUND */
    .stApp {{
        {bg_css}
        background-size: contain; /* Try 'contain' to prevent stretching, or back to 'cover' */
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-color: #000; /* Fallback color */
    }}
    
    /* HIDE HEADER/FOOTER */
    header, footer {{ display: none !important; }}
    
    /* MAIN CONTAINER FOR BUTTONS */
    .block-container {{
        display: flex;
        flex-direction: column;
        justify-content: flex-end; /* Push content to bottom */
        align-items: center;
        height: 90vh !important; /* Use viewport height */
        padding-bottom: 5vh !important;
    }}

    /* STYLE THE BUTTONS */
    div[data-testid="stButton"] > button {{
        background-color: rgba(255, 255, 255, 0.1); /* Semi-transparent white */
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 25px; /* Rounded corners */
        padding: 15px 30px;
        font-size: 18px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%; /* Full width in their columns */
    }}
    
    div[data-testid="stButton"] > button:hover {{
        background-color: rgba(255, 255, 255, 0.2);
        border-color: white;
        transform: translateY(-2px); /* Slight lift effect */
    }}
    </style>
    """, unsafe_allow_html=True)

    # --- 3. The Buttons ---
    # Use columns to arrange them horizontally
    c1, c2, c3 = st.columns([1, 1, 1.5]) # Give Guest Mode a bit more space
    
    with c1: 
        if st.button("Log In", key="btn_login", use_container_width=True):
            st.toast("Login coming soon!")
            
    with c2: 
        if st.button("Sign Up", key="btn_signup", use_container_width=True):
            st.toast("Signup coming soon!")
            
    with c3:
        # PRIMARY ACTION
        if st.button("Guest Mode ✈️", key="btn_guest", use_container_width=True):
            st.session_state['page'] = 'main'
            st.rerun()