import os
import django
from django.conf import settings
from django.template import loader

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

def test_template_exists():
    try:
        t = loader.get_template('add_review.html')
        print("✅ SUCCESS: add_review.html template found and loaded.")
        
        # Check for specific elements in the template
        content = t.template.source
        if 'star-rating' in content and 'star-icon' in content:
            print("✅ SUCCESS: Interactive star rating found in template.")
        else:
            print("❌ ERROR: Missing interactive star rating in template.")
            
        if 'Order {{ order.order_id }}' in content:
            print("✅ SUCCESS: Order ID placeholder found.")
            
    except Exception as e:
        print(f"❌ ERROR: Failed to load template: {e}")

if __name__ == "__main__":
    test_template_exists()
