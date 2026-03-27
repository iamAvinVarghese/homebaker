import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order
from django.db.models import Count

orders = Order.objects.all()
total = orders.count()
pending = orders.filter(status='pending').count()

print(f"Total Orders: {total}")
print(f"Pending Orders: {pending}")

print("\nDetailed Status Count:")
status_counts = orders.values('status').annotate(count=Count('id'))
for s in status_counts:
    print(f"{s['status']}: {s['count']}")

print("\nOrders by Customer:")
customer_orders = orders.values('customer__username').annotate(count=Count('id'))
for c in customer_orders:
    print(f"{c['customer__username']}: {c['count']}")
