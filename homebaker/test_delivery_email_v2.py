import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order, User, UserProfile
from django.utils import timezone
from main.views_customer import verify_order_acceptance
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
import decimal

def test_delivery_email():
    # 1. Setup Data
    username = 'testcustomer_email_new1'
    # Use a unique username to avoid conflicts
    user, created = User.objects.get_or_create(username=username, email='test@example.com')
    if created:
        UserProfile.objects.create(user=user, role='customer', phone_number='1234567890')
    
    # 2. Create Order
    order_id = '#TEST_EMAIL_101'
    Order.objects.filter(order_id=order_id).delete()
    order = Order.objects.create(
        customer=user,
        order_id=order_id,
        status='awaiting_confirmation',
        total_amount=decimal.Decimal('150.00'),
        delivery_date=timezone.now().date(),
        delivery_address='Test Address',
        confirmation_otp='1234'
    )
    
    # 3. Simulate Request
    factory = RequestFactory()
    request = factory.post(f'/verify-order-acceptance/{order_id}/', {'otp': '1234'})
    request.user = user
    
    # Add messages support
    setattr(request, 'session', {})
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)

    # Clear outbox
    from django.conf import settings
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []

    # 4. Call View
    print(f"Executing verify_order_acceptance for {order_id}...")
    verify_order_acceptance(request, order_id)

    # 5. Verify Results
    order.refresh_from_db()
    print(f"Order Status: {order.status}")
    
    if order.status == 'delivered':
        print("SUCCESS: Order status updated to delivered.")
    else:
        print(f"FAILURE: Order status is {order.status}, expected delivered.")

    print(f"Emails in outbox: {len(mail.outbox)}")
    if len(mail.outbox) > 0:
        email = mail.outbox[0]
        print(f"Email Subject: {email.subject}")
        if 'delivered successfully' in email.body or 'delivered successfully' in str(email.alternatives):
             print("SUCCESS: Delivery success message found in email.")
        else:
             print("FAILURE: Delivery success message NOT found in email content.")
             print(f"Body snippet: {email.body[:100]}")
    else:
        print("FAILURE: No emails sent.")

if __name__ == '__main__':
    test_delivery_email()
