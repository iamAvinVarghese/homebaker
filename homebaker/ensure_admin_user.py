
import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile

def ensure_admin_user():
    username = '1234567890'
    password = 'aaaaaa12'
    
    try:
        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True # Optional, but good for admin
        user.save()
        
        # Ensure profile exists
        profile, p_created = UserProfile.objects.get_or_create(user=user, defaults={'phone_number': username})
        profile.role = 'admin'
        profile.phone_number = username
        profile.is_phone_verified = True
        profile.save()
        
        if created:
            print(f"Successfully created admin user: {username}")
        else:
            print(f"Successfully updated admin user: {username}")
            
    except Exception as e:
        print(f"Error configuring admin user: {e}")

if __name__ == '__main__':
    ensure_admin_user()
