import os
from google import genai
from dotenv import load_dotenv

# 1. Load your key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ No API Key found in .env!")
else:
    print(f"✅ Key found: {api_key[:5]}...")
    
    # 2. Ask Google what models are available
    try:
        client = genai.Client(api_key=api_key)
        print("\n🔍 Scanning for available models...")
        
        # List models and filter for "generateContent" support
        for model in client.models.list():
            print(f" - Found: {model.name}")
            
    except Exception as e:
        print(f"\n❌ API Error: {e}")