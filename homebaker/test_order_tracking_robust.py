import os
import django
from django.db.models import Q

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order, User
from django.test import RequestFactory
from main.views_customer import order_tracking

def test_robustness():
    print("--- Testing Order Tracking Robustness ---")
    
    # Setup test data
    order_id = '#55422'
    try:
        order = Order.objects.get(order_id=order_id)
        customer = order.customer
        baker = order.items.first().cake.baker
        staff = User.objects.filter(is_staff=True).first()
        other_user = User.objects.exclude(id__in=[customer.id, baker.id if baker else -1, staff.id if staff else -1]).first()
        
        factory = RequestFactory()
        
        test_cases = [
            ("Customer (Correct owner)", customer, "#55422", 200),
            ("Customer (No # in ID)", customer, "55422", 200),
            ("Customer (With whitespace)", customer, " #55422 ", 200),
            ("Baker (Assigned)", baker, "#55422", 200),
            ("Staff (Any order)", staff, "#55422", 200),
            ("Other User (Unauthorized)", other_user, "#55422", 404),
            ("Invalid Order ID", customer, "#99999", 404),
        ]
        
        for name, user, oid, expected_status in test_cases:
            if not user:
                print(f"{name}: Skipping (User not found)")
                continue
                
            request = factory.get(f'/order-tracking/{oid}/')
            request.user = user
            
            try:
                response = order_tracking(request, oid)
                status = response.status_code
                print(f"{name}: Expected {expected_status}, Got {status} - {'PASSED' if status == expected_status else 'FAILED'}")
            except Exception as e:
                print(f"{name}: Error: {e}")
                
    except Order.DoesNotExist:
        print(f"Error: Target order {order_id} not found in database.")

if __name__ == "__main__":
    test_robustness()
