import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.ai_utils import CakeDesigner

def test_designer():
    requirements = {
        'flavor': 'Red Velvet',
        'shape': 'Heart',
        'size': '2kg',
        'design_style': 'Romantic Vintage',
        'primary_colors': 'Deep Red and Gold',
        'extra_instructions': 'Add delicate edible gold pearls and lace textures.',
        'estimated_price': 2500
    }
    
    print("Testing AI Designer with requirements:")
    for k, v in requirements.items():
        print(f"  {k}: {v}")
    
    print("\nGenerating design...")
    result = CakeDesigner.generate_custom_design(requirements)
    
    print("\n--- RESULTS ---")
    print(f"Summary: {result.get('summary')}")
    print(f"Image Description: {result.get('image_description')}")
    print(f"Design Instructions: {result.get('design_instructions')}")
    print(f"Estimated Price: {result.get('estimated_price')}")
    
    if result.get('images'):
        print(f"\nImages Generated: {len(result['images'])}")
        for i, url in enumerate(result['images']):
            print(f"  Image {i+1}: {url}")
    else:
        print("\nNO IMAGES GENERATED (Check API keys/connectivity)")

if __name__ == "__main__":
    test_designer()
