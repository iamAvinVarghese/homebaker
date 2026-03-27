import requests

def test_pollinations():
    prompt = "A beautiful birthday cake, detailed, realistic, 8k"
    url = f"https://image.pollinations.ai/prompt/{prompt}?width=1024&height=768&seed=123&nologo=true&model=flux"
    print(f"Testing URL: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers.get('Content-Type')}")
        if response.status_code == 200:
            print("Success! Pollinations is reachable.")
        else:
            print(f"Failed: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_pollinations()
