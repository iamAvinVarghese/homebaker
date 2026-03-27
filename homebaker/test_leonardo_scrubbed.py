import os
import django
import requests
import time
import re
import urllib.parse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from django.conf import settings

def scrub_brands(text):
    """Genericizes known brand names to avoid moderation filters"""
    brands = [
        'batman', 'superman', 'spiderman', 'marvel', 'disney', 'mickey', 
        'star wars', 'pokemon', 'pikachu', 'barbie', 'frozen', 'elsa',
        'netflix', 'google', 'apple', 'starbucks', 'nike', 'adidas'
    ]
    scrubbed = text
    for brand in brands:
        # Case-insensitive replacement with generic terms
        scrubbed = re.sub(brand, "superhero character" if brand in ['batman', 'superman', 'spiderman'] else "popular character", scrubbed, flags=re.IGNORECASE)
    return scrubbed

def test_leonardo_live():
    print("--- Testing Leonardo with Scrubbed Batman Prompt ---")
    raw_prompt = "A beautiful 1kg Round cake in black. It features a batman design suitable for a birthday. The frosting is smooth and elegant."
    scrubbed_prompt = scrub_brands(raw_prompt)
    print(f"Original: {raw_prompt}")
    print(f"Scrubbed: {scrubbed_prompt}")
    
    enhanced_prompt = f"{scrubbed_prompt}, detailed, realistic, 8k, professional food photography, cinematic lighting, appetizing"
    
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {settings.LEONARDO_API_KEY}"
    }
    
    payload = {
        "prompt": enhanced_prompt,
        "modelId": "6b645e3a-d64f-4341-a6d8-7a3690fbf042",
        "width": 1024,
        "height": 768,
        "num_images": 4,
        "alchemy": True,
        "presetStyle": "PHOTOGRAPHY"
    }
    
    print("Sending request to Leonardo (4 images + Alchemy)...")
    response = requests.post(url, json=payload, headers=headers)
    print(f"Response Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Job Data: {data}")
    else:
        print(f"Error Response: {response.text}")

if __name__ == "__main__":
    test_leonardo_live()
