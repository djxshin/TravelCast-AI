import streamlit as st
import base64
import os

#
def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception as e:
        return None

#
def show_splash():
    # --- 1. ROBUST IMAGE FINDER ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    
    possible_paths = [
        os.path.join(root_dir, "splashpage.jpg"),
        os.path.join(current_dir, "splashpage.jpg"),
        "splashpage.jpg"
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
        st.error(f"Debug: Could not find 'splashpage.jpg' in {root_dir}")

    # --- 2. CSS: Background & Button Positioning ---
    st.markdown(f"""
    <style>
    /* FORCE FULL SCREEN BACKGROUND */
    .stApp {{
        {bg_css}
        background-size: cover; /* Keeps the image filling the screen */
        background-position: bottom center; /* Prioritizes the bottom of the image */
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* HIDE HEADER/FOOTER */
    header, footer {{ display: none !important; }}
    
    /* PUSH CONTENT TO BOTTOM */
    /* REDUCED padding to move buttons up slightly. Adjust this value if needed. */
    .block-container {{
        padding-top: 70vh !important; 
        padding-bottom: 5vh !important;
    }}

    /* DEBUGGING: MAKE BUTTONS VISIBLE */
    div[data-testid="stButton"] > button {{
        background-color: rgba(255, 0, 0, 0.4); /* Semi-transparent RED for debugging */
        color: white; /* Show text */
        border: 2px solid red; /* Red border */
        height: 60px;
        width: 100%;
        cursor: pointer;
        font-weight: bold;
    }}
    
    div[data-testid="stButton"] > button:hover {{
        background-color: rgba(255, 0, 0, 0.6);
    }}
    </style>
    """, unsafe_allow_html=True)

    # --- 3. The Buttons ---
    c1, c2, c3 = st.columns([1, 1, 1.2])
    
    with c1: 
        if st.button("Log In", key="btn_login", use_container_width=True):
            st.toast("Login coming soon!")
            
    with c2: 
        if st.button("Sign Up", key="btn_signup", use_container_width=True):
            st.toast("Signup coming soon!")
            
    with c3:
        # PRIMARY ACTION
        if st.button("Guest Mode", key="btn_guest", use_container_width=True):
            st.session_state['page'] = 'main'
            st.rerun()