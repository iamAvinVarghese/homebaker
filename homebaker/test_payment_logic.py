import os
import django
import sys
from decimal import Decimal

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order, OrderItem, Cake, CustomCakeRequest, BakerProfile, UserProfile
from django.contrib.auth.models import User
from django.utils import timezone

def test_custom_completion():
    print("Testing Custom Request Completion Logic...")
    
    # Setup test data
    customer, _ = User.objects.get_or_create(username='test_customer_payment')
    baker_user, _ = User.objects.get_or_create(username='test_baker_payment')
    up, _ = UserProfile.objects.get_or_create(user=baker_user, defaults={'role': 'baker'})
    baker_profile, _ = BakerProfile.objects.get_or_create(
        user_profile=up,
        defaults={'shop_name': 'Test Shop'}
    )
    
    # Create a custom request
    custom_req = CustomCakeRequest.objects.create(
        customer=customer,
        baker=baker_profile,
        request_type='AI',
        description='Test Custom Cake',
        status='ACCEPTED',
        price_quote=1500
    )
    print(f"Created Custom Request ID: {custom_req.id}, Initial Status: {custom_req.status}")
    
    # Create a cake representing this request
    cake = Cake.objects.create(
        name=f"Custom Cake Request #{custom_req.id}",
        baker=baker_user,
        price=1500,
        occasion='custom'
    )
    
    # Create an order simulating checkout completion
    order = Order.objects.create(
        customer=customer,
        delivery_date=timezone.now().date(),
        delivery_address="Test",
        total_amount=1550,
        status='pending'
    )
    
    OrderItem.objects.create(
        order=order,
        cake=cake,
        quantity=1,
        unit_price=1500,
        subtotal=1500
    )
    
    # --- SIMULATE THE FIX LOGIC ---
    print("\nSimulating checkout completion logic...")
    for item in order.items.all():
        if item.cake.name.startswith("Custom Cake Request #"):
            try:
                request_id_str = item.cake.name.split("#")[-1]
                request_id = int(request_id_str)
                CustomCakeRequest.objects.filter(id=request_id).update(status='COMPLETED')
                print(f"Matched ID {request_id}. Updated status.")
            except (ValueError, IndexError):
                print("Failed to parse ID")

    # Refresh and check
    custom_req.refresh_from_db()
    print(f"Final Custom Request Status: {custom_req.status}")
    
    if custom_req.status == 'COMPLETED':
        print("\nSUCCESS: Custom request marked as COMPLETED.")
    else:
        print("\nFAILURE: Custom request status unchanged.")

if __name__ == "__main__":
    test_custom_completion()
