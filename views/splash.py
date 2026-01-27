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
    # --- 1. ROBUST IMAGE FINDER ---
    # Get the absolute path to the 'travelcast-ai' root folder
    current_dir = os.path.dirname(os.path.abspath(__file__)) # This is .../views
    root_dir = os.path.dirname(current_dir)                  # This is .../travelcast-ai
    
    # Check specifically for 'splashpage.jpg' based on your screenshot
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

    # --- 2. CSS: Full Screen & Button Positioning ---
    if img_path:
        bin_str = get_base64(img_path)
        # Note: Changed to image/jpeg to match your file extension
        bg_css = f'background-image: url("data:image/jpeg;base64,{bin_str}");'
    else:
        # Fallback if image is somehow still missing
        bg_css = 'background-color: #1e1e1e;'
        st.error(f"Debug: Could not find 'splashpage.jpg' in {root_dir}")

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
    /* Adjusted padding to align with the buttons in your image */
    .block-container {{
        padding-top: 78vh !important; 
        padding-bottom: 5vh !important;
    }}

    /* CUSTOMIZE BUTTONS TO MATCH IMAGE AESTHETIC */
    div[data-testid="stButton"] > button {{
        background-color: rgba(60, 40, 30, 0.01); /* Invisible click area */
        color: transparent; /* Hide text so we see the image buttons */
        border: none;
        height: 60px;
        width: 100%;
        cursor: pointer;
    }}
    
    div[data-testid="stButton"] > button:hover {{
        background-color: rgba(255, 255, 255, 0.1); /* Subtle hover effect */
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 12px;
    }}
    </style>
    """, unsafe_allow_html=True)

    # --- 3. The Buttons (Invisible Overlays) ---
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