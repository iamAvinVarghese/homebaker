import os
import django
from django.conf import settings
import google.generativeai as genai
import requests

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

def test_gemini_2_5():
    print("--- Testing Gemini 2.5-flash ---")
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    try:
        response = model.generate_content("Say hello from Gemini 2.5")
        print(f"Success: {response.text}")
    except Exception as e:
        print(f"Failed: {e}")

def test_leonardo_prioritization():
    print("\n--- Testing Leonardo API Prioritization ---")
    if not settings.LEONARDO_API_KEY:
        print("Leonardo API Key missing in settings.")
        return

    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {settings.LEONARDO_API_KEY}"
    }
    try:
        # Just check if the key is valid by hitting the me endpoint or similar if possible, 
        # or just verify the code logic in ai_utils.py manually since we can't easily poll here.
        # Let's try to list models as a connection test.
        response = requests.get("https://cloud.leonardo.ai/api/rest/v1/me", headers=headers)
        if response.status_code == 200:
            print(f"Leonardo API Connection Success: {response.json().get('user', {}).get('username', 'N/A')}")
        else:
            print(f"Leonardo API Connection Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Leonardo API Connection Error: {e}")

if __name__ == "__main__":
    test_gemini_2_5()
    test_leonardo_prioritization()
