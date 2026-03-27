import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order
from django.contrib.auth.models import User

order_id = '#55422'
print(f"Checking for order {order_id}...")

order = Order.objects.filter(order_id=order_id).first()
if order:
    print(f"Order found!")
    print(f"Customer: {order.customer.username}")
    print(f"Status: {order.status}")
    print(f"Total Amount: {order.total_amount}")
else:
    print("Order NOT found.")
    print("Recent orders:")
    for o in Order.objects.all().order_by('-created_at')[:5]:
        print(f"- {o.order_id} (Customer: {o.customer.username})")

users = User.objects.all()
print(f"\nTotal users: {users.count()}")
for u in users:
    print(f"- {u.username} (Staff: {u.is_staff})")
