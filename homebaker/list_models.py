import google.generativeai as genai
import os
from django.conf import settings
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

genai.configure(api_key=settings.GEMINI_API_KEY)

with open('model_list.txt', 'w') as f:
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                f.write(f"{m.name}\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
