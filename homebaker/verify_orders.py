import os
import django
import sys
import random

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order, OrderItem, Cake, User

def verify_order_details():
    print("--- Verifying Order Details Display Logic ---")
    
    # Check if we have any orders
    orders = Order.objects.all().prefetch_related('items__cake')
    if not orders.exists():
        print("No orders found to verify.")
        return

    for order in orders[:5]:
        print(f"\nOrder ID: {order.order_id}")
        items = order.items.all()
        print(f"Items Count: {items.count()}")
        
        for item in items:
            cake = item.cake
            print(f"  - Item: {cake.name}")
            print(f"    Flavor: {cake.flavor}")
            print(f"    Quantity: {item.quantity} kg")
            print(f"    Unit Price: ₹{item.unit_price}")
            print(f"    Message: {item.message_on_cake or 'None'}")
            
            # Check custom fallback logic
            if cake.name.startswith("Custom Cake Request #"):
                print(f"    [CUSTOM] Description (Extra Info): {cake.description[:50]}...")
            else:
                print(f"    [REGULAR] Cake Name: {cake.name}")

    print("\nVerification Complete.")

if __name__ == "__main__":
    verify_order_details()
