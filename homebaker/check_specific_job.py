import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from django.conf import settings

def check_job(job_id):
    url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{job_id}"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {settings.LEONARDO_API_KEY}"
    }
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    check_job("547dfde0-ce4b-4348-82d5-866818ab2108")
