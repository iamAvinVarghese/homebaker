import os
import django
import requests
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from django.conf import settings

def test_leonardo_with_alchemy():
    print("--- Testing Leonardo with Alchemy ---")
    if not settings.LEONARDO_API_KEY:
        print("API Key missing.")
        return

    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {settings.LEONARDO_API_KEY}"
    }
    
    payload = {
        "prompt": "A beautiful birthday cake",
        "modelId": "6b645e3a-d64f-4341-a6d8-7a3690fbf042",
        "width": 1024,
        "height": 768,
        "num_images": 1,
        "alchemy": True,
        "presetStyle": "PHOTOGRAPHY"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_leonardo_with_alchemy()
