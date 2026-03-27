import os
import django
import sys
from datetime import timedelta

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order
from django.contrib.auth.models import User
from django.utils import timezone

def test_timeline():
    # Get or create a test user
    user, _ = User.objects.get_or_create(username='testuser_timeline')
    
    statuses = ['pending', 'confirmed', 'baking', 'packing', 'out_for_delivery', 'delivered', 'cancelled']
    
    for status in statuses:
        print(f"\n--- Testing Status: {status} ---")
        order = Order(
            customer=user,
            delivery_date=timezone.now().date() + timedelta(days=1),
            delivery_address="Test Address",
            total_amount=1000,
            status=status
        )
        # Manually set created_at and status_updated_at for testing since we are not saving
        order.created_at = timezone.now() - timedelta(hours=2)
        order.status_updated_at = timezone.now() - timedelta(minutes=30)
        
        timeline = order.get_status_timeline()
        for step in timeline:
            state = "[X]" if step['is_completed'] else "[ ]"
            current = " (CURRENT)" if step.get('is_current') else ""
            error = " (ERROR)" if step.get('is_error') else ""
            time_str = step['time'].strftime('%H:%M') if step['time'] else "N/A"
            print(f"{state} {step['status']}: {time_str}{current}{error}")

if __name__ == "__main__":
    test_timeline()
