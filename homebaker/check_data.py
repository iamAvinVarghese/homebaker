import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import CakeSize, OrderItem

print("--- CakeSize Data ---")
for cs in CakeSize.objects.all():
    print(f"ID: {cs.id}, Size: {cs.size}, Multiplier: {cs.multiplier}")

print("\n--- Recent OrderItem Data ---")
for item in OrderItem.objects.order_by('-id')[:5]:
    size_str = item.size.size if item.size else "None"
    print(f"ID: {item.id}, Cake: {item.cake.name}, Size: {size_str}, Qty: {item.quantity}, Price: {item.unit_price}, Subtotal: {item.subtotal}")
