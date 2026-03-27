import os
import django
import requests
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from django.conf import settings

def test_leonardo_full_flow():
    print("--- Testing Leonardo Full Generation Flow ---")
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
        "prompt": "A beautiful birthday cake, professional food photography, 8k",
        "modelId": "6b645e3a-d64f-4341-a6d8-7a3690fbf042",
        "width": 1024,
        "height": 768,
        "num_images": 1
    }
    
    print("1. Creating Generation Job...")
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code != 200:
        print("Failed to create job.")
        return
        
    try:
        generation_id = response.json()['sdGenerationJob']['generationId']
        print(f"Job ID: {generation_id}")
    except KeyError:
        print("Could not find generationId in response.")
        return

    print("2. Polling for results...")
    for i in range(5):
        time.sleep(5)
        status_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
        status_response = requests.get(status_url, headers=headers)
        print(f"Polling {i+1} status: {status_response.status_code}")
        
        if status_response.status_code == 200:
            data = status_response.json()
            # Inspect structure
            print(f"Keys in response: {data.keys()}")
            if 'generations_by_pk' in data:
                status = data['generations_by_pk']['status']
                print(f"Status: {status}")
                if status == 'COMPLETE':
                    imgs = data['generations_by_pk']['generated_images']
                    print(f"Success! Found {len(imgs)} images.")
                    for img in imgs:
                        print(f"URL: {img['url']}")
                    return
            else:
                print("Missing 'generations_by_pk' in response.")
                print(f"Full Data: {data}")
        else:
            print(f"Polling error: {status_response.text}")

if __name__ == "__main__":
    test_leonardo_full_flow()
