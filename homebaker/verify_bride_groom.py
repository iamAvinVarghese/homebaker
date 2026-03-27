import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.ai_utils import CakeDesigner
from django.conf import settings

def test_bride_groom():
    print(f"DEBUG: LEONARDO_API_KEY present in settings: {bool(settings.LEONARDO_API_KEY)}")
    print("--- Testing Bride and Groom Prompt ---")
    reqs = {
        'size': '0.5kg',
        'shape': 'Tall',
        'flavor': 'White',
        'primary_colors': 'White',
        'occasion': 'Wedding/Birthday',
        'design_style': 'Elegant',
        'message_on_cake': '',
        'extra_instructions': 'A beautiful 0.5kg Tall cake in white. It features a bride and groom on the top design.'
    }
    
    print("Generating design...")
    try:
        result = CakeDesigner.generate_custom_design(reqs)
        print("\n--- RESULTS ---")
        print(f"Summary: {result.get('summary')}")
        image_urls = result.get('image_urls', [])
        print(f"Total Images: {len(image_urls)}")
        for url in image_urls:
            print(f"URL: {url}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_bride_groom()
