import os
import google.generativeai as genai
from decouple import config

# Load env
try:
    api_key = config('GEMINI_API_KEY')
    print(f"API Key found: {api_key[:5]}...{api_key[-5:]}")
except Exception as e:
    print(f"Error loading API Key: {e}")
    exit(1)

genai.configure(api_key=api_key)

try:
    print("Listing available models:")
    found_model = None
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            if 'gemini' in m.name.lower() and not found_model:
                found_model = m.name

    if found_model:
        with open('working_model.txt', 'w') as f:
            f.write(found_model)
        print(f"\nTesting with model: {found_model}")
        model = genai.GenerativeModel(found_model)
        response = model.generate_content("Hello")
        print("Success!")
        print(f"Response: {response.text}")
    else:
        print("No suitable Gemini model found.")

except Exception as e:
    print(f"Error: {e}")
