import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import BakerProfile, Order, Review
from django.db.models import Sum

for baker in BakerProfile.objects.all():
    user = baker.user_profile.user
    baker_orders = Order.objects.filter(items__cake__baker=user).distinct()
    total_orders = baker_orders.count()
    total_delivered = baker_orders.filter(status='delivered').count()
    
    # Revenue
    revenue = baker_orders.filter(payment_status='paid').aggregate(total=Sum('subtotal'))['total'] or 0
    
    print(f"Baker: {user.username} | Shop: {baker.shop_name}")
    print(f"  Orders: {total_orders} | Delivered: {delivered_count if 'delivered_count' in locals() else total_delivered}")
    print(f"  Revenue: {revenue} | Profit calculated in profile: {baker.total_profit}")
    print(f"  Rating in profile: {baker.average_rating}")
    
    reviews = Review.objects.filter(cake__baker=user)
    print(f"  Reviews ({reviews.count()} total):")
    for r in reviews:
        print(f"    - ID: {r.id}, Rating: {r.rating}, Approved: {r.is_approved}")
    
    print("-" * 30)
