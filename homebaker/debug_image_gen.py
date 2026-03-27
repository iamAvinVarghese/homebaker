import os
import sys
import urllib.parse
import urllib.request
import random

# Setup Django environment
sys.path.append(r'd:\HomeBakerProject\homebaker')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
import django
django.setup()

from main.ai_utils import CakeDesigner

print("--- DEBUG START ---")

# 1. Test Basic Connectivity
simple_url = "https://image.pollinations.ai/prompt/cake?width=800&height=600&nologo=true"
print(f"\nTesting Simple URL: {simple_url}")
try:
    req = urllib.request.Request(simple_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
    with urllib.request.urlopen(req) as response:
        print(f"Simple URL Status: {response.getcode()}")
except Exception as e:
    print(f"Simple URL Failed: {e}")

# 2. Test Actual Generation
requirements = {
    'size': '2kg',
    'shape': 'Round',
    'flavor': 'Chocolate',
    'primary_colors': 'Red',
    'occasion': 'Birthday',
    'design_style': 'Modern',
    'message_on_cake': 'Happy Birthday',
    'extra_instructions': 'None'
}

print("\nGenerating cake design...")
try:
    result = CakeDesigner.generate_custom_design(requirements)
    image_url = result.get('image_url', '')
    print(f"Generated URL: {image_url}")
    print(f"URL Length: {len(image_url)}")
    
    if image_url:
        print("\nFetching Generated URL...")
        req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        with urllib.request.urlopen(req) as response:
            print(f"Generated URL Status: {response.getcode()}")
            print(f"Content Type: {response.info().get_content_type()}")
            print(f"Bytes: {len(response.read())}")
            
except Exception as e:
    print(f"Generation/Fetch Failed: {e}")

print("\n--- DEBUG END ---")
