import os
import django
import requests
import json
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

def check_quota():
    print("--- Checking Leonardo.ai API Quota ---")
    api_key = settings.LEONARDO_API_KEY
    if not api_key:
        print("Error: LEONARDO_API_KEY not found in settings.")
        return

    url = "https://cloud.leonardo.ai/api/rest/v1/me"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # print(json.dumps(data, indent=2)) # Full response for debugging
            
            user_details_list = data.get('user_details', [])
            if not user_details_list:
                print("Error: No user details found in response.")
                print(f"Full response: {data}")
                return
                
            user_details = user_details_list[0]
            user = user_details.get('user', {})
            username = user.get('username', 'N/A')
            
            # Check for various token fields
            api_tokens = user_details.get('apiCreditTokens')
            subscription_tokens = user_details.get('subscriptionTokens')
            
            print(f"User: {username}")
            print(f"API Credit Tokens: {api_tokens}")
            print(f"Subscription Tokens: {subscription_tokens}")
            
            if api_tokens == 0 and subscription_tokens == 0:
                print("CRITICAL: You have 0 tokens left. API quota reached.")
            else:
                print("Status: You have active tokens for generation.")
        else:
            print(f"Error fetching quota: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception while checking quota: {e}")

if __name__ == "__main__":
    check_quota()
