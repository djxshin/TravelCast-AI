# utils/logic.py

# --- EXISTING LOGIC (KEPT SAFE) ---
def calculate_capacity_metrics(luggage_counts, duration, shopping_intent, formal_count, walking_level, avg_temp=None):
    CAPACITY_MAP = { "backpack": 20, "carry_on": 40, "checked": 100 }
    total_capacity = (luggage_counts['backpack'] * CAPACITY_MAP['backpack']) + \
                     (luggage_counts['carry_on'] * CAPACITY_MAP['carry_on']) + \
                     (luggage_counts['checked'] * CAPACITY_MAP['checked'])
    
    base_daily_load = 3.5 
    bulk_multiplier = 1.0
    if avg_temp is not None:
        if avg_temp < 50: bulk_multiplier = 1.4
        elif avg_temp > 75: bulk_multiplier = 0.8
    
    daily_load = base_daily_load * bulk_multiplier
    tech_kit = 2.0 
    shoes_vol = 3.0 if walking_level == "High" else 1.5
    formal_vol = 4.0 * formal_count 
    
    estimated_load = (duration * daily_load) + tech_kit + shoes_vol + formal_vol
    
    SHOPPING_RESERVE = { "None": 0.0, "Light": 0.10, "Medium": 0.20, "Heavy": 0.30 }
    reserved_space = total_capacity * SHOPPING_RESERVE[shopping_intent]
    
    final_used = estimated_load
    usage_pct = (final_used + reserved_space) / total_capacity if total_capacity > 0 else 1.1
    
    return {
        "total_L": total_capacity, "used_L": round(final_used, 1),
        "reserved_L": round(reserved_space, 1), 
        "usage_pct": min(usage_pct, 1.0),
        "is_overpacked": usage_pct > 1.0, 
        "bulk_multiplier": bulk_multiplier
    }

def get_trip_context(arrival, depart, shopping_intent, luggage_counts):
    delta = depart - arrival
    duration = max(1, delta.days + 1)
    shopping_note = "Standard packing."
    if shopping_intent == "Heavy":
        if luggage_counts['checked'] > 0: shopping_note = "User plans HEAVY shopping. Suggest packing checked bag only 50% full."
        elif luggage_counts['carry_on'] > 0: shopping_note = "CRITICAL: Heavy shopping with Carry-on. Reduce clothing by 30%."
        else: shopping_note = "CRITICAL: Heavy shopping with Backpack. Minimalist capsule wardrobe only."
    return duration, shopping_note

# --- NEW FUNCTION (ADDED TO FIX IMPORT ERROR) ---
def get_packing_profile(duration, is_business, gender, style_preference):
    """
    Generates a structured dictionary for the AI.
    """
    profile = {
        "trip_duration_days": duration,
        "is_business_trip": is_business,
        "user_gender": gender,
        "style_preference": style_preference,
        "formal_count": 0, 
        "shopping_note": "Ensure space is left for shopping."
    }
    
    if duration > 7:
        profile['laundry_note'] = "Trip exceeds 7 days. Suggest laundry logic."
    if is_business:
        profile['formal_count'] = 2 
        
    return profile