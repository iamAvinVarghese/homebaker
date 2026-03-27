import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import CustomCakeRequest, OrderItem

def sync_past_orders():
    print("Syncing past custom request statuses...")
    
    # Find all ACCEPTED requests
    accepted_requests = CustomCakeRequest.objects.filter(status='ACCEPTED')
    count = 0
    
    for req in accepted_requests:
        # Construct the cake name we search for
        cake_name = f"Custom Cake Request #{req.id}"
        
        # Check if any order item exists with this cake name
        exists = OrderItem.objects.filter(cake__name=cake_name).exists()
        
        if exists:
            req.status = 'COMPLETED'
            # Also try to find a relevant baker message if missing, though typically it should be there
            req.save()
            print(f"Updated Request #{req.id} to COMPLETED")
            count += 1
            
    print(f"Total updated: {count}")

if __name__ == "__main__":
    sync_past_orders()
