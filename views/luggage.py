import streamlit as st
from utils.weather import get_weather_data
from utils.ai import generate_smart_packing_list
# CRITICAL: This import works now because you created the file in Step 1
from utils.logic import get_packing_profile

def show_luggage_page():
    st.markdown("## 🎒 Luggage & Logistics")
    
    # --- 1. USER INPUTS ---
    col1, col2 = st.columns(2)
    with col1:
        trip_duration = st.slider("Trip Duration (Days)", 1, 30, 7)
    with col2:
        # Default capacity 100L (Medium Check-in)
        total_capacity = st.number_input("Total Luggage Capacity (Liters)", value=100, step=10)

    # --- 2. GET CONTEXT (Weather & Profile) ---
    city = st.session_state.get('city', 'Unknown')
    weather_data = st.session_state.get('weather_data', None)
    
    # Default to 20°C if no weather data found
    avg_temp = 20
    if weather_data and 'current' in weather_data:
        avg_temp = weather_data['current'].get('temp_c', 20)

    # --- 3. SMART SPACE CALCULATION ---
    # Determine if it's a "Cold" or "Warm" trip
    is_cold = avg_temp < 15  # Threshold: 15°C (59°F)
    
    # Base Usage: Clothes typically take ~40% of a bag
    base_usage = 0.40 
    
    if is_cold:
        # --- COLD WEATHER LOGIC ---
        # Penalty: Winter clothes are bulky (+20% usage)
        weather_penalty = 0.20
        # Bonus: User wears Coat & Boots on plane (Saves 15%)
        wear_on_plane_bonus = 0.15 
        
        wearable_item = "Winter Coat & Boots"
        final_usage_ratio = base_usage + weather_penalty - wear_on_plane_bonus
    else:
        # --- WARM WEATHER LOGIC ---
        # Penalty: None (Clothes are thin)
        weather_penalty = 0.0
        # Bonus: User wears Sneakers & Hoodie on plane (Saves 5%)
        wear_on_plane_bonus = 0.05
        
        wearable_item = "Sneakers & Hoodie"
        final_usage_ratio = base_usage + weather_penalty - wear_on_plane_bonus

    # Safety Cap: Ensure usage is realistic (between 30% and 90%)
    final_usage_ratio = max(0.3, min(0.9, final_usage_ratio))
    
    # Calculate Liters
    used_volume = total_capacity * final_usage_ratio
    shopping_potential = total_capacity - used_volume

    # --- 4. VISUALIZATION FUNCTION ---
    def get_capacity_visualization(liters, is_cold_trip):
        items = []
        remaining = liters
        
        if is_cold_trip:
            # WINTER SHOPPING (Big items take big space)
            n_parkas = int(remaining // 15) # Assume Jacket is ~15L
            if n_parkas > 0:
                items.append(f"🧥 {n_parkas}x Jacket{'s' if n_parkas > 1 else ''}")
                remaining -= (n_parkas * 15)
                
            n_boots = int(remaining // 10) # Assume Boots are ~10L
            if n_boots > 0:
                items.append(f"🥾 {n_boots}x Boot Pair{'s' if n_boots > 1 else ''}")
        else:
            # SUMMER SHOPPING (Small items)
            n_sneakers = int(remaining // 8) # Assume Sneakers are ~8L
            if n_sneakers > 0:
                items.append(f"👟 {n_sneakers}x Kicks")
                remaining -= (n_sneakers * 8)
                
            n_shirts = int(remaining) # Assume T-Shirt is ~1L
            if n_shirts > 0:
                items.append(f"👕 {n_shirts}x Tees")

        if not items: 
            return "Small souvenirs only!"
        return "  +  ".join(items[:3])

    # --- 5. RENDER THE UI ---
    st.markdown("### ✅ Ready to Pack!")
    
    # Progress Bar representing Packed vs. Free space
    st.progress(final_usage_ratio)
    
    # The "Visualizer" Card
    visual_text = get_capacity_visualization(shopping_potential, is_cold)
    
    st.markdown(f"""
    <div style="
        background-color: #1a1a1a; 
        border: 1px solid #333; 
        border-radius: 12px; 
        padding: 20px; 
        margin-top: 15px; 
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h3 style="margin:0; color: #66bb6a;">🛍️ Available Space: {shopping_potential:.1f} L</h3>
            <span style="background-color: #2e7d32; color: white; padding: 5px 10px; border-radius: 15px; font-size: 0.8em; font-weight: bold;">
                ✈️ Smart Packer Bonus Active
            </span>
        </div>

        <p style="color: #bbb; font-size: 0.9em; margin-bottom: 15px; border-left: 3px solid #4a90e2; padding-left: 10px;">
            We calculated your space assuming you <b>wear your {wearable_item}</b> on the plane.
            <br><i>(Comfort Tip: Use the 'Subway Peel' strategy—take the heavy layer off once seated!)</i>
        </p>

        <div style="background-color: #252525; padding: 10px; border-radius: 8px;">
            <p style="margin:0; color: #fff; font-size: 1.1em;">
                Room left for: <b style="color: #ffd700;">{visual_text}</b>
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 6. WARNINGS ---
    st.warning("⚠️ Checked Bag Warning: Watch your weight limit (50lb/23kg).")

    # --- 7. GENERATE BUTTON ---
    if st.button("Generate Optimized List", type="primary", use_container_width=True):
        with st.spinner("🤖 AI is curating your wardrobe..."):
            
            # 1. Gather Profile (Using the imported logic function)
            profile = get_packing_profile(
                duration=trip_duration,
                is_business=False, 
                gender="Neutral",  
                style_preference="Standard"
            )
            
            # 2. Add Shopping Context to Profile so AI knows
            profile['shopping_context'] = f"User has {shopping_potential:.1f}L space for shopping. Suggest items like {visual_text}."
            
            # 3. Call AI
            if 'genai_client' in st.session_state:
                result = generate_smart_packing_list(city, weather_data, profile, st.session_state['genai_client'])
                st.session_state['packing_list'] = result
                st.rerun()
            else:
                st.error("AI Client not initialized. Please return to Home.")

    # --- 8. DISPLAY RESULTS ---
    if 'packing_list' in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state['packing_list'])