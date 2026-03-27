import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from django.db import transaction
from main.models import User, UserProfile, Order, Review, Cake, BakerProfile, AuditLog, OTP, CustomCakeRequest, Wallet, Notification

TARGET_USERNAMES = [
    'test_baker_payment',
    'test_customer_payment',
    'testuser_timeline',
    '0000000000' # Delivery Assistant
]

def cleanup():
    with transaction.atomic():
        print("Starting database cleanup...")
        
        users_to_delete = User.objects.filter(username__in=TARGET_USERNAMES)
        user_ids = list(users_to_delete.values_list('id', flat=True))
        
        # Get phone numbers for OTP cleanup
        phone_numbers = list(UserProfile.objects.filter(user__id__in=user_ids).values_list('phone_number', flat=True))
        
        print(f"Targeting {len(user_ids)} users: {TARGET_USERNAMES}")
        
        # 1. Delete Cakes associated with these users (since baker is a ForeignKey to User)
        # We delete them first to be safe, although cascade might handle it if defined.
        cakes_deleted, _ = Cake.objects.filter(baker__id__in=user_ids).delete()
        print(f"Deleted {cakes_deleted} cakes.")
        
        # 2. Delete Audit Logs referencing these users or with null user (orphans)
        audit_logs_deleted, _ = AuditLog.objects.filter(user__id__in=user_ids).delete()
        print(f"Deleted {audit_logs_deleted} audit logs for target users.")
        
        orphaned_audit_logs, _ = AuditLog.objects.filter(user=None).delete()
        print(f"Deleted {orphaned_audit_logs} orphaned audit logs.")
        
        # 3. Delete OTPs for these phone numbers
        otps_deleted, _ = OTP.objects.filter(phone_number__in=phone_numbers).delete()
        print(f"Deleted {otps_deleted} OTP records.")
        
        # 4. Delete the User objects
        # This triggers CASCADE for UserProfile, Order, Review, Wallet, Notification, CustomCakeRequest
        users_deleted, _ = users_to_delete.delete()
        print(f"Deleted {users_deleted} User objects (and cascaded data).")
        
        print("\nCleanup completed successfully!")

if __name__ == "__main__":
    cleanup()
