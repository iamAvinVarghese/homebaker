import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.ai_utils import CakeDesigner

def verify_integration():
    print("--- Verifying Full AI Designer Integration ---")
    reqs = {
        'size': '1kg',
        'shape': 'Round',
        'flavor': 'Chocolate',
        'primary_colors': 'Black and Yellow',
        'occasion': 'Birthday',
        'design_style': 'Batman Theme',
        'message_on_cake': 'Happy Birthday',
        'extra_instructions': 'Make it look cool'
    }
    
    print("Generating design (this may take up to 60s)...")
    try:
        result = CakeDesigner.generate_custom_design(reqs)
        
        print("\n--- RESULTS ---")
        print(f"Summary: {result.get('summary')}")
        print(f"Description (First 100 chars): {result.get('image_description', '')[:100]}...")
        
        image_urls = result.get('image_urls', [])
        print(f"Total Images Generated: {len(image_urls)}")
        
        leo_count = 0
        poll_count = 0
        for url in image_urls:
            if 'leonardo' in url:
                leo_count += 1
            elif 'pollinations' in url:
                poll_count += 1
        
        print(f"Leonardo.ai Images: {leo_count}")
        print(f"Pollinations.ai Images: {poll_count}")
        
        if leo_count > 0:
            print("SUCCESS: Leonardo.ai is working correctly!")
        else:
            print("WARNING: Leonardo.ai failed, fell back to Pollinations.")
            
        print(f"First Image URL: {image_urls[0]}")
        
    except Exception as e:
        print(f"FAILED with exception: {e}")

if __name__ == "__main__":
    verify_integration()
