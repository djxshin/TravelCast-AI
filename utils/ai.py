import os
from google import genai
from google.genai import types

def generate_smart_packing_list(city_label, weather_json, profile_data, client):
    if not client: return "Error: Google API Key not found."

    # --- 1. MODEL CONFIGURATION (The Fixes) ---
    # PRIMARY: We pin 'gemini-1.5-flash-002' (Specific stable version, not 'latest')
    # This prevents the AI behavior from changing randomly overnight.
    env_model = os.getenv("GEMINI_MODEL")
    primary_model = env_model if env_model else "gemini-1.5-flash-002"
    
    # BACKUP: If Primary fails (e.g. Rate Limit or Deprecation), we fall back to this.
    # 'gemini-1.5-flash-8b' is a tiny, fast model that is very reliable as a backup.
    fallback_model = "gemini-1.5-flash-8b"

    # --- 2. PROMPT CONSTRUCTION ---
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
    4. PRO TIP: Provide specific advice on managing indoor/outdoor temperature transitions (e.g., the 'Subway Peel' strategy).
    5. {formal_instruction}
    
    OUTPUT FORMAT (Strict Markdown):
    ### 🌤️ Daily Planner
    * **Morning:** [Max 15 words. Specific layering tactic.]
    * **Afternoon:** [Max 15 words. Specific layering tactic.]
    * **Evening:** [Max 15 words. Specific layering tactic.]
    
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
    
    # --- 3. EXECUTION WITH SAFETY NET ---
    try:
        # Attempt 1: The Primary Model
        response = client.models.generate_content(model=primary_model, contents=prompt)
        return response.text
    
    except Exception as e:
        print(f"⚠️ Primary model '{primary_model}' failed: {e}")
        
        # Attempt 2: The Fallback Model
        try:
            print(f"🔄 Switching to backup model: '{fallback_model}'...")
            response = client.models.generate_content(model=fallback_model, contents=prompt)
            # We append a tiny note so you know the backup fired (useful for debugging)
            return response.text + "\n\n*(Generated via Backup Model)*"
            
        except Exception as e2:
            # Absolute Failure (Both models down)
            return f"❌ AI Service Unavailable. Please check API Key or Quota. Error: {str(e2)}"