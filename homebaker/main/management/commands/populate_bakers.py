from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import BakerProfile, Cake
from django.utils.crypto import get_random_string
import os
from django.conf import settings
import shutil

class Command(BaseCommand):
    help = 'Populate test data for 5 bakers with unique cakes'

    def handle(self, *args, **kwargs):
        # Base image path
        base_image_name = 'test_cake_image.png' # Assuming this is the name from generate_image
        base_image_path = os.path.join(settings.BASE_DIR, 'media', 'cakes', base_image_name)
        
        # Ensure media/cakes directory exists
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'cakes'), exist_ok=True)
        
        # Check if base image exists, if not, create a dummy one or use exiting
        # For this script we will assume the agent will copy the generated image to this location first.
        # But to be safe, I'll create a dummy file if it doesn't exist for testing.
        if not os.path.exists(base_image_path):
             # Try to find any image in the directory to use as base
            existing_images = [f for f in os.listdir(os.path.join(settings.MEDIA_ROOT, 'cakes')) if f.endswith(('.png', '.jpg', '.jpeg'))]
            if existing_images:
                base_image_path = os.path.join(settings.MEDIA_ROOT, 'cakes', existing_images[0])
            else:
                self.stdout.write(self.style.ERROR('No base image found in media/cakes. Please add an image first.'))
                return

        for i in range(1, 6):
            phone_number = f'{i:010d}' # 0000000001, 0000000002...
            username = f'baker_{phone_number}'
            email = f'baker{i}@example.com'
            password = 'password123'

            # Create User
            user, created = User.objects.get_or_create(username=username, email=email)
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
            else:
                self.stdout.write(self.style.WARNING(f'User {username} already exists'))

            # Create/Update UserProfile
            # Models say UserProfile is OneToOne with User
            from main.models import UserProfile
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            user_profile.phone_number = phone_number
            user_profile.role = 'baker'
            user_profile.is_phone_verified = True
            user_profile.save()

            # Create BakerProfile
            baker_profile, created = BakerProfile.objects.get_or_create(user_profile=user_profile)
            if created:
                baker_profile.shop_name = f"Baker {i}'s Shop"
                baker_profile.address = f"Street {i}, City"
                baker_profile.city = "City"
                baker_profile.pincode = "123456"
                baker_profile.status = 'approved' # Auto approve
                baker_profile.save()
                self.stdout.write(self.style.SUCCESS(f'Created baker profile for {username}'))

            # Create 2 Cakes per baker
            for j in range(1, 3):
                cake_name = f'Delicious Cake {i}-{j}'
                
                # Create unique image
                unique_image_name = f'cake_{phone_number}_{j}.png'
                unique_image_path = os.path.join(settings.MEDIA_ROOT, 'cakes', unique_image_name)
                
                # Copy base image to unique path
                if os.path.exists(base_image_path):
                    try:
                        shutil.copy2(base_image_path, unique_image_path)
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Failed to copy image: {e}'))

                # Create Cake
                # Cake model links to User via 'baker' field
                cake, created = Cake.objects.get_or_create(
                    baker=user, 
                    name=cake_name,
                    defaults={
                        'flavor': 'chocolate', # Default flavor
                        'occasion': 'birthday', # Default occasion
                        'price': 500 + (i * 10) + (j * 5),
                        'image': f'cakes/{unique_image_name}',
                        'description': f'A wonderful cake from baker {phone_number}',
                        'is_available': True,
                        'stock_quantity': 10
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created cake: {cake_name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Cake {cake_name} already exists'))

        self.stdout.write(self.style.SUCCESS('Successfully populated test data'))
