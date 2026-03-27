import os
import django
from django.db.models import Sum
import sys

# Force UTF-8 for stdout
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order, BakerProfile

def inspect_revenue():
    with open('revenue_report.txt', 'w', encoding='utf-8') as f:
        f.write("Checking bakers...\n")
        for baker in BakerProfile.objects.all():
            orders = Order.objects.filter(items__cake__baker=baker.user_profile.user, payment_status='paid')
            revenue = orders.aggregate(total=Sum('subtotal'))['total'] or 0
            
            if revenue > 0:
                f.write(f"Baker: {baker.user_profile.user.username}\n")
                f.write(f"Total Revenue: {revenue}\n")
                f.write("Orders contributing to revenue:\n")
                for order in orders:
                    f.write(f" - Order #{order.order_id}: {order.subtotal} (Subtotal) (Date: {order.created_at.strftime('%Y-%m-%d %H:%M')})\n")

if __name__ == '__main__':
    inspect_revenue()
