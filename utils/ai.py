import os
from google import genai

def generate_smart_packing_list(city_label, weather_json, profile_data, client):
    if not client: return "Error: Google API Key not found."

    # --- REVERTED CONFIGURATION ---
    # Going back to the original model alias that was working for you.
    target_model = "gemini-flash-latest"

    formal_instruction = "No formal events."
    if profile_data.get('formal_count', 0) > 0:
        formal_instruction = f"IMPORTANT: User has {profile_data['formal_count']} formal events. Include exactly {profile_data['formal_count']} formal outfits."

    prompt = f"""
    Act as an Expert Travel Logistics Manager.
    DESTINATION: {city_label}
    WEATHER: {weather_json.get('daily', 'N/A')}
    TRIP PROFILE: {profile_data}
    CONSTRAINTS: 
    1. {profile_data.get('shopping_note', 'Standard packing')}
    2. BREVITY: Keep item descriptions under 10 words. Functional only.
    3. DAILY PLANNER: This must be SHORT and punchy. Maximum 15 words per time block.
    4. PRO TIP: Provide specific advice on managing indoor/outdoor temperature transitions.
    5. {formal_instruction}
    
    OUTPUT FORMAT (Strict Markdown):
    ### 🌤️ Daily Planner
    * **Morning:** [Specific layering tactic.]
    * **Afternoon:** [Specific layering tactic.]
    * **Evening:** [Specific layering tactic.]
    
    ### ✈️ Wear On Plane (Space Savers)
    * **[Item 1]:** [Brief reason]
    * **[Item 2]:** [Brief reason]
    
    ### 🎒 The Packing List
    | Category | Item | Qty | Notes |
    | :--- | :--- | :--- | :--- |
    | Tops | ... | ... | ... |
    
    ### 💡 Pro Tip
    [Write a detailed, strategic tip here.]
    """
    
    # --- EXECUTION ---
    try:
        # Simple, direct call. No fallbacks.
        response = client.models.generate_content(model=target_model, contents=prompt)
        return response.text
    except Exception as e:
        return f"❌ AI Error: {str(e)}"