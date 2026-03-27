
import os
import django
import sys

# Setup Django environment
sys.path.append('d:\\HomeBakerProject\\homebaker')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.ai_utils import CakeDesigner


def test_generation():
    from django.conf import settings
    print(f"API Key configured: {bool(settings.GEMINI_API_KEY)}")

    requirements = {
        'size': '2kg',
        'shape': 'Round',
        'flavor': 'Spiderman Chocolate',
        'primary_colors': 'Red and Blue',
        'occasion': 'Birthday',
        'design_style': 'Superhero',
        'message_on_cake': 'Happy Birthday',
        'extra_instructions': 'Web designs'
    }
    
    print("Testing CakeDesigner.generate_custom_design with Bing Source...")
    try:
        result = CakeDesigner.generate_custom_design(requirements)
        print("\nResult:")
        image_url = result.get('image_url')
        print(f"Image URL: {image_url}")
        print(f"Description: {result.get('image_description')}")
        
        # Check if URL is accessible (Bing should be 200)
        if image_url:
            import requests
            print(f"Testing URL connectivity...")
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(image_url, headers=headers, timeout=10)
                print(f"URL Status Code: {response.status_code}")
                if response.status_code == 200:
                    print(f"Image Size: {len(response.content)} bytes")
                    if "bing.net" in image_url:
                        print("SUCCESS: Image source is Bing.")
                else:
                    print("Failed to download image.")
            except Exception as req_e:
                print(f"URL Connection Error: {req_e}")
                
    except Exception as e:
        print(f"\nException occurred: {e}")

if __name__ == "__main__":
    test_generation()
