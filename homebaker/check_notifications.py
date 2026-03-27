import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order, Notification

order_id = '#39599'
try:
    order = Order.objects.get(order_id=order_id)
    notifications = Notification.objects.filter(order=order)
    print(f"Notifications for {order_id}:")
    for n in notifications:
        print(f"  Type: {n.notification_type}")
        print(f"  Title: {n.title}")
        print(f"  Message: {n.message}")
        print("-" * 20)
except Order.DoesNotExist:
    print(f"Order {order_id} not found")
