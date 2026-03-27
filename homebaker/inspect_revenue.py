import os
import django
from django.db.models import Sum

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order, BakerProfile

def inspect_revenue():
    print("Checking bakers...")
    for baker in BakerProfile.objects.all():
        orders = Order.objects.filter(items__cake__baker=baker.user_profile.user, payment_status='paid')
        revenue = orders.aggregate(total=Sum('subtotal'))['total'] or 0
        
        if revenue > 0:
            print(f"Baker: {baker.user_profile.user.username}")
            print(f"Total Revenue: {revenue}")
            print("Orders contributing to revenue:")
            for order in orders:
                print(f" - Order #{order.order_id}: {order.subtotal} (Subtotal) (Date: {order.created_at.strftime('%Y-%m-%d %H:%M')})")

if __name__ == '__main__':
    inspect_revenue()
