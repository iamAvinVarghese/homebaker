import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import BakerProfile, Review, Order, Cake
from django.db.models import Count, Sum

print("--- Detailed Baker Check ---")
for baker in BakerProfile.objects.all():
    user = baker.user_profile.user
    orders_count = Order.objects.filter(items__cake__baker=user).distinct().count()
    delivered_count = Order.objects.filter(items__cake__baker=user, status='delivered').distinct().count()
    
    # Check if this matches user screenshot (5 orders, 1 delivered)
    if orders_count == 5 and delivered_count == 1:
        print(f"MATCH FOUND: Baker {baker.shop_name} (User: {user.username})")
        print(f"  Orders: {orders_count}, Delivered: {delivered_count}")
        print(f"  Rating in Profile: {baker.average_rating}")
        
        reviews = Review.objects.filter(cake__baker=user)
        print(f"  Total Reviews (including unapproved): {reviews.count()}")
        for r in reviews:
            print(f"    - ID: {r.id}, Rating: {r.rating}, Approved: {r.is_approved}, Cake: {r.cake.name}")
            
        # Check calculation
        approved_reviews = reviews.filter(is_approved=True)
        if approved_reviews.exists():
            avg = sum(r.rating for r in approved_reviews) / approved_reviews.count()
            print(f"  Manual Calculation (sum/count): {avg}")
        else:
            print("  No approved reviews found.")

if BakerProfile.objects.count() == 0:
    print("No bakers found in database.")
