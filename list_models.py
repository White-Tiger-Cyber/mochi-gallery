import os
import pprint
from google import genai
from dotenv import load_dotenv

# 1. Load Environment (if .env exists)
load_dotenv()

# 2. Get the Key (Using the standard ALL CAPS name)
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in environment.")
    print("Please run: export GEMINI_API_KEY='your_actual_key'")
    exit()

print(f"✅ Key found. Connecting to Google AI...")

try:
    client = genai.Client(api_key=api_key)
    
    print(f"\n{'MODEL ID':<40} | {'DISPLAY NAME'}")
    print("-" * 70)

    # 3. Iterate through models
    for m in client.models.list():
        # clean_name calculation
        # Some SDK versions use 'name', others might use 'display_name'
        # We use getattr to be safe.
        mid = getattr(m, 'name', 'Unknown-ID').replace('models/', '')
        dname = getattr(m, 'display_name', 'Unknown-Name')
        
        # Check generation methods safely
        # If the attribute is missing, we assume it's a generation model and print it anyway
        methods = getattr(m, 'supported_generation_methods', [])
        
        # If the list is missing (AttributeError fix) or contains 'generateContent'
        if not methods or "generateContent" in methods:
            print(f"{mid:<40} | {dname}")

except Exception as e:
    print(f"\n❌ detailed error info:")
    print(e)
