import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order
from django.db import transaction

def refine_orders():
    with transaction.atomic():
        print("Refining orders...")
        
        # We want to keep exactly 11 orders, and none should be pending.
        # Current state: 11 delivered, 5 cancelled.
        # Action: Delete all orders that are NOT 'delivered'
        
        target_orders = Order.objects.exclude(status='delivered')
        count = target_orders.count()
        deleted, _ = target_orders.delete()
        
        print(f"Deleted {deleted} non-delivered orders.")
        
        final_count = Order.objects.all().count()
        print(f"Final order count: {final_count}")
        
        if final_count == 11:
            print("Success: Total orders reached 11.")
        else:
            print(f"Warning: Unexpected final count {final_count}")

if __name__ == "__main__":
    refine_orders()
