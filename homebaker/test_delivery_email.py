import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order, User, Cake, BakerProfile, UserProfile, OrderItem
from django.utils import timezone
from main.views_customer import verify_order_acceptance
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
import decimal

def test_delivery_email():
    # 1. Setup Data
    username = 'testcustomer_email'
    user, created = User.objects.get_or_create(username=username, email='test@example.com')
    if created:
        UserProfile.objects.create(user=user, role='customer')
    
    # Clear debug log
    log_path = 'email_debug.log'
    if os.path.exists(log_path):
        with open(log_path, 'w') as f:
            f.truncate(0)

    # 2. Create Order
    order_id = '#TEST12345'
    Order.objects.filter(order_id=order_id).delete()
    order = Order.objects.create(
        customer=user,
        order_id=order_id,
        status='awaiting_confirmation',
        total_amount=decimal.Decimal('100.00'),
        delivery_date=timezone.now().date(),
        delivery_address='Test Address',
        confirmation_otp='9999'
    )
    
    # 3. Simulate Request
    factory = RequestFactory()
    request = factory.post(f'/verify-order-acceptance/{order_id}/', {'otp': '9999'})
    request.user = user
    
    # Add messages support
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)

    # 4. Call View
    print("Executing verify_order_acceptance...")
    verify_order_acceptance(request, order_id)

    # 5. Verify Results
    order.refresh_from_db()
    print(f"Order Status: {order.status}")
    
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            log_content = f.read()
            if 'delivered successfully' in log_content:
                print("SUCCESS: Delivery success message found in email log.")
            else:
                print("FAILURE: Delivery success message NOT found in email log.")
                print("Log Content:")
                print(log_content)
    else:
        print("FAILURE: email_debug.log not found.")

if __name__ == '__main__':
    test_delivery_email()
