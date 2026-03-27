import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order

order_id = '#55422'
try:
    order = Order.objects.get(order_id=order_id)
    print(f"Order: {order.order_id}")
    print(f"Customer: {order.customer.username}")
    
    bakers = set()
    for item in order.items.all():
        if item.cake.baker:
            bakers.add(item.cake.baker.username)
    
    print(f"Bakers assigned: {list(bakers)}")
except Order.DoesNotExist:
    print(f"Order {order_id} not found.")
except Exception as e:
    print(f"Error: {e}")
