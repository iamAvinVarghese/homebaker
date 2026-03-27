import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile

def restore():
    username = '0000000000'
    print(f"Restoring user: {username}...")
    
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': 'Delivery',
            'last_name': 'Assistant',
            'email': '',
        }
    )
    
    if created or user.password == '':
        user.set_password('password123')
        user.save()
        print("User created/password set.")
    else:
        print("User already exists.")
        
    profile, p_created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'phone_number': username,
            'role': 'delivery_assistant',
            'is_phone_verified': True,
        }
    )
    
    if p_created:
        print("UserProfile created with role 'delivery_assistant'.")
    else:
        profile.role = 'delivery_assistant'
        profile.phone_number = username
        profile.is_phone_verified = True
        profile.save()
        print("UserProfile updated.")

    print("Delivery Assistant restored successfully!")

if __name__ == "__main__":
    restore()
