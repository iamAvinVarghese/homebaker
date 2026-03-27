import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import BakerProfile, Review, Cake
from django.db.models import Avg

print("--- Baker Ratings Diagnostic ---")
bakers = BakerProfile.objects.all()
for baker in bakers:
    user = baker.user_profile.user
    reviews = Review.objects.filter(cake__baker=user, is_approved=True)
    avg_calc = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    print(f"Baker: {baker.shop_name} (User: {user.username})")
    print(f"  Profile Rating: {baker.average_rating}")
    print(f"  Profile Total Reviews: {baker.total_reviews}")
    print(f"  Calculated Avg from Reviews: {avg_calc}")
    print(f"  Actual Review Count: {reviews.count()}")
    for r in reviews:
        print(f"    - Rating: {r.rating} (Review ID: {r.id}, Cake: {r.cake.name})")

print("\n--- Cake Ratings ---")
cakes = Cake.objects.all()
for cake in cakes:
    print(f"Cake: {cake.name} (Baker: {cake.baker.username if cake.baker else 'N/A'})")
    print(f"  Rating: {cake.average_rating} ({cake.total_reviews} reviews)")
