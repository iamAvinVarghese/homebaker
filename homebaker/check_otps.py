import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order

order_ids = ['#39599', '#40041']
for oid in order_ids:
    try:
        order = Order.objects.get(order_id=oid)
        print(f"Order: {oid}")
        print(f"  Status: {order.status}")
        print(f"  Delivery OTP: '{order.delivery_otp}'")
        print(f"  Confirmation OTP: '{order.confirmation_otp}'")
    except Order.DoesNotExist:
        print(f"Order: {oid} - NOT FOUND")
