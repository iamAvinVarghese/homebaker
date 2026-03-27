import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import User

from main.models import User, UserProfile, Order, Review

users = User.objects.all().order_by('id')
with open('users_list.txt', 'w') as f:
    f.write(f"{'ID':<5} | {'Username':<25} | {'Role':<15} | {'Name':<20} | {'Orders':<8} | {'Reviews':<8}\n")
    f.write("-" * 100 + "\n")
    for user in users:
        try:
            profile = user.profile
            role = profile.role
            name = f"{user.first_name} {user.last_name}".strip() or "N/A"
        except (UserProfile.DoesNotExist, AttributeError):
            role = "N/A"
            name = "N/A"
        
        order_count = Order.objects.filter(customer=user).count()
        review_count = Review.objects.filter(customer=user).count()
        
        f.write(f"{user.id:<5} | {user.username:<25} | {role:<15} | {name:<20} | {order_count:<8} | {review_count:<8}\n")
print("User list with data counts written to users_list.txt")
