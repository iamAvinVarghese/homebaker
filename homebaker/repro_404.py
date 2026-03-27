import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.models import Order
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

def simulate_tracking(username, order_id_from_url):
    print(f"\nSimulating tracking for user '{username}' with URL order_id '{order_id_from_url}'")
    try:
        user = User.objects.get(username=username)
        # Normalization logic from view
        search_id = order_id_from_url if order_id_from_url.startswith('#') else f'#{order_id_from_url}'
        print(f"Normalized search_id: '{search_id}'")
        
        # Simulating view logic
        if user.is_staff:
            order = Order.objects.get(order_id=search_id)
        else:
            order = Order.objects.get(order_id=search_id, customer=user)
        print(f"SUCCESS: Found order {order.order_id}")
    except User.DoesNotExist:
        print(f"Error: User '{username}' not found")
    except Order.DoesNotExist:
        print(f"404: Order matches NOT found (Ownership or ID mismatch)")
    except Exception as e:
        print(f"Error: {e}")

# Check the specific order from the screenshot
# We saw earlier it belongs to '3000000000'
simulate_tracking('3000000000', '#55422')
simulate_tracking('3000000000', '55422')

# Check with a different user
# Let's find another user
other_user = User.objects.exclude(username='3000000000').first()
if other_user:
    simulate_tracking(other_user.username, '55422')
