import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order, User, UserProfile, Wallet
from django.utils import timezone
from decimal import Decimal

def recall_data():
    username = '0000000000'
    try:
        user = User.objects.get(username=username)
        profile = user.profile
    except User.DoesNotExist:
        print("User not found.")
        return

    print(f"Recalling data for {username}...")

    # 1. Restore Profile Picture
    photo_path = 'profile_pics/delivery-rider-in-simple-flat-personal-profile-icon-or-symbol-people-concep_3MRxAi6.jpg'
    profile.profile_picture = photo_path
    profile.save()
    print("Profile picture restored.")

    # 2. Restore Wallet Transactions for delivered orders
    # Each delivered order should have a credit to the assistant for the delivery_charge
    delivered_orders = Order.objects.filter(status='delivered').order_by('created_at')
    
    # First, clear existing transactions for this user to avoid duplicates if any were half-created
    Wallet.objects.filter(user=user).delete()
    
    count = 0
    for order in delivered_orders:
        if order.delivery_charge > 0:
            Wallet.add_transaction(
                user=user,
                transaction_type='credit',
                amount=order.delivery_charge,
                source='order',
                description=f'Delivery Fee for Order {order.order_id}',
                order=order
            )
            count += 1
    
    print(f"Restored {count} wallet transactions.")
    print(f"Current wallet balance: {Wallet.get_user_balance(user)}")

    print("Data recall completed!")

if __name__ == "__main__":
    recall_data()
