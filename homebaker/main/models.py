from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random


# User Profile Model (extends Django User)
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('baker', 'Baker'),
        ('admin', 'Admin'),
        ('delivery_assistant', 'Delivery Assistant'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_phone_verified = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    is_suspended = models.BooleanField(default=False)
    email_otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    default_address = models.TextField(blank=True, help_text="Default delivery address")
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_account_locked(self):
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False
    
    def lock_account(self, hours=24):
        """Lock account for specified hours"""
        self.account_locked_until = timezone.now() + timedelta(hours=hours)
        self.save()
    
    def unlock_account(self):
        """Unlock account and reset failed attempts"""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save()
    
    def increment_failed_attempts(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account()
        self.save()
    
    def reset_failed_attempts(self):
        """Reset failed login attempts on successful login"""
        self.failed_login_attempts = 0
        self.save()
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


# Baker Profile Model (extends UserProfile for bakers)
class BakerProfile(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='baker_profile')
    shop_name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    license_number = models.CharField(max_length=50, blank=True, unique=True, db_index=True)
    fssai_certificate = models.ImageField(upload_to='baker_documents/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    accepts_custom_orders = models.BooleanField(default=True, help_text="Accept custom cake orders")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, help_text="Platform commission %")
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def update_rating(self):
        """Update average rating based on all reviews for this baker's cakes"""
        from django.db.models import Avg, Sum
        from .models import Review
        
        # Get all approved reviews for all of this baker's cakes
        reviews = Review.objects.filter(
            cake__baker=self.user_profile.user,
            is_approved=True
        )
        
        result = reviews.aggregate(Avg('rating'))
        self.average_rating = result['rating__avg'] or 0.00
        
        # Total reviews count
        self.total_reviews = reviews.count()
        self.save(update_fields=['average_rating', 'total_reviews'])
    
    def __str__(self):
        return f"{self.shop_name} - {self.user_profile.user.username}"
    
    def calculate_profit(self, revenue, expenses):
        """Calculate profit after expenses and commission"""
        commission = revenue * (self.commission_rate / 100)
        return revenue - expenses - commission
    
    class Meta:
        verbose_name = "Baker Profile"
        verbose_name_plural = "Baker Profiles"


# Cake Size Model
class CakeSize(models.Model):
    SIZE_CHOICES = [
        ('small', 'Small (0.5 kg)'),
        ('medium', 'Medium (1 kg)'),
        ('large', 'Large (2 kg)'),
        ('xlarge', 'Extra Large (3 kg)'),
    ]
    
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, unique=True)
    multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.00, help_text="Price multiplier")
    
    def __str__(self):
        return self.get_size_display()
    
    class Meta:
        verbose_name = "Cake Size"
        verbose_name_plural = "Cake Sizes"


# Cake Model
class Cake(models.Model):
    FLAVOR_CHOICES = [
        ('chocolate', 'Chocolate'),
        ('vanilla', 'Vanilla'),
        ('red_velvet', 'Red Velvet'),
        ('strawberry', 'Strawberry'),
        ('butterscotch', 'Butterscotch'),
        ('fruit', 'Fruit'),
        ('black_forest', 'Black Forest'),
        ('pineapple', 'Pineapple'),
        ('mango', 'Mango'),
    ]
    
    OCCASION_CHOICES = [
        ('birthday', 'Birthday'),
        ('wedding', 'Wedding'),
        ('anniversary', 'Anniversary'),
        ('graduation', 'Graduation'),
        ('custom', 'Custom'),
        ('festival', 'Festival'),
    ]
    
    name = models.CharField(max_length=200)
    flavor = models.CharField(max_length=50, choices=FLAVOR_CHOICES)
    occasion = models.CharField(max_length=50, choices=OCCASION_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='cakes/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True, help_text="External image URL if not uploading")
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    baker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cakes', help_text="Baker who created this cake")
    views_count = models.PositiveIntegerField(default=0)
    order_count = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def increment_views(self):
        """Increment view count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def increment_orders(self):
        """Increment order count"""
        self.order_count += 1
        self.save(update_fields=['order_count'])
    
    def update_rating(self):
        """Update average rating from reviews"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            self.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0.00
            self.total_reviews = reviews.count()
        else:
            self.average_rating = 0.00
            self.total_reviews = 0
        self.save(update_fields=['average_rating', 'total_reviews'])
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Cake"
        verbose_name_plural = "Cakes"


# Order Model
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('awaiting_confirmation', 'Awaiting Confirmation'),
        ('confirmed', 'Confirmed'),
        ('baking', 'Baking'),
        ('packing', 'Packing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order_id = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    delivery_date = models.DateField()
    delivery_address = models.TextField()
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Discount applied via coupon code")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True, default='wallet')
    delivery_otp = models.CharField(max_length=4, null=True, blank=True, help_text="4-digit delivery OTP")
    confirmation_otp = models.CharField(max_length=4, null=True, blank=True, help_text="4-digit order confirmation OTP")
    otp_verified = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    status_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.order_id} - {self.customer.username}"
    
    def save(self, *args, **kwargs):
        if not self.order_id:
            # Generate unique order ID
            while True:
                order_id = f"#{random.randint(10000, 99999)}"
                if not Order.objects.filter(order_id=order_id).exists():
                    self.order_id = order_id
                    break
        
        # Update status timestamp when status changes
        if self.pk:
            old_order = Order.objects.get(pk=self.pk)
            if old_order.status != self.status:
                self.status_updated_at = timezone.now()
        else:
            self.status_updated_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_status_timeline(self):
        """Get status change timeline with all steps"""
        # Define the sequence of statuses
        all_statuses = [
            ('pending', 'Order Placed'),
            ('confirmed', 'Confirmed'),
            ('baking', 'Baking'),
            ('packing', 'Packing'),
            ('out_for_delivery', 'Out for Delivery'),
            ('delivered', 'Delivered')
        ]
        
        # If cancelled, handle separately
        if self.status == 'cancelled':
            return [
                {'status': 'Order Placed', 'time': self.created_at, 'is_completed': True},
                {'status': 'Cancelled', 'time': self.status_updated_at, 'is_completed': True, 'is_error': True}
            ]
            
        timeline = []
        status_rank = {s[0]: i for i, s in enumerate(all_statuses)}
        current_rank = status_rank.get(self.status, 0)
        
        for i, (status_code, status_label) in enumerate(all_statuses):
            is_completed = i <= current_rank
            time = None
            
            if status_code == 'pending':
                time = self.created_at
            elif status_code == self.status:
                time = self.status_updated_at
            elif status_code == 'delivered' and self.status == 'delivered':
                time = self.delivered_at or self.status_updated_at
                
            timeline.append({
                'status': status_label,
                'time': time,
                'is_completed': is_completed,
                'is_current': status_code == self.status
            })
            
        return timeline
    
    @property
    def clean_id(self):
        """Returns order_id without the # prefix for safe URL navigation"""
        if self.order_id.startswith('#'):
            return self.order_id[1:]
        return self.order_id

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders"


# Order Item Model (for cart/checkout with multiple items)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    cake = models.ForeignKey(Cake, on_delete=models.CASCADE, related_name='order_items')
    size = models.ForeignKey(CakeSize, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    message_on_cake = models.CharField(max_length=200, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        # Calculate subtotal
        size_multiplier = self.size.multiplier if self.size else Decimal('1.00')
        self.subtotal = self.unit_price * size_multiplier * Decimal(str(self.quantity))
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.order.order_id} - {self.cake.name} x{self.quantity}"
    
    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"


# Expense Model (for baker expense tracking)
class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('ingredients', 'Ingredients'),
        ('packaging', 'Packaging'),
        ('delivery', 'Delivery'),
        ('utilities', 'Utilities'),
        ('equipment', 'Equipment'),
        ('marketing', 'Marketing'),
        ('other', 'Other'),
    ]
    
    baker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses', limit_choices_to={'profile__role': 'baker'})
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    expense_date = models.DateField()
    receipt = models.ImageField(upload_to='expenses/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.baker.username} - {self.category} - ₹{self.amount}"
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"


# Review Model (for ratings and reviews)
class Review(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    cake = models.ForeignKey(Cake, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    photo = models.ImageField(upload_to='reviews/', blank=True, null=True, help_text="Photo after delivery")
    is_approved = models.BooleanField(default=True)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.customer.username} - {self.cake.name} - {self.rating}⭐"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update cake rating
        self.cake.update_rating()
        # Update baker rating
        if self.cake.baker and hasattr(self.cake.baker, 'profile') and hasattr(self.cake.baker.profile, 'baker_profile'):
            self.cake.baker.profile.baker_profile.update_rating()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        unique_together = ['order', 'cake', 'customer']


# Wallet Model (for customer wallet system)
class Wallet(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]
    
    TRANSACTION_SOURCE_CHOICES = [
        ('recharge', 'Wallet Recharge'),
        ('refund', 'Order Refund'),
        ('order', 'Order Payment'),
        ('cashback', 'Cashback'),
        ('commission', 'Commission'),
        ('withdrawal', 'Withdrawal'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    source = models.CharField(max_length=20, choices=TRANSACTION_SOURCE_CHOICES)
    description = models.CharField(max_length=200)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet_transactions')
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - ₹{self.amount}"
    
    @classmethod
    def get_user_balance(cls, user):
        """Get current wallet balance for user"""
        from decimal import Decimal
        transactions = cls.objects.filter(user=user).order_by('-created_at')
        if transactions.exists():
            return transactions.first().balance_after
        return Decimal('0.00')
    
    @classmethod
    def add_transaction(cls, user, transaction_type, amount, source, description, order=None):
        """Add wallet transaction and update balance"""
        from decimal import Decimal
        current_balance = cls.get_user_balance(user)
        amount = Decimal(str(amount))
        
        if transaction_type == 'credit':
            new_balance = current_balance + amount
        else:  # debit
            new_balance = current_balance - amount
        
        return cls.objects.create(
            user=user,
            transaction_type=transaction_type,
            amount=amount,
            source=source,
            description=description,
            order=order,
            balance_after=new_balance
        )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Wallet Transaction"
        verbose_name_plural = "Wallet Transactions"


# Notification Model
class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('order_placed', 'Order Placed'),
        ('order_confirmed', 'Order Confirmed'),
        ('order_baking', 'Order Baking'),
        ('order_ready', 'Order Ready'),
        ('order_delivered', 'Order Delivered'),
        ('order_cancelled', 'Order Cancelled'),
        ('review_received', 'Review Received'),
        ('baker_approved', 'Baker Approved'),
        ('baker_rejected', 'Baker Rejected'),
        ('payment_received', 'Payment Received'),
        ('low_stock', 'Low Stock Alert'),
        ('custom_request_accepted', 'Custom Request Accepted'),
        ('custom_request_rejected', 'Custom Request Rejected'),
        ('ticket_resolved', 'Support Ticket Resolved'),
        ('coupon_launched', 'New Coupon Launched'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_target_url(self):
        """Returns the appropriate URL for this notification based on user role and context"""
        from django.urls import reverse
        
        # Priority 1: Specific Order links
        if self.order:
            if self.user.profile.role == 'baker':
                return reverse('baker_orders')
            elif self.user.profile.role == 'delivery_assistant':
                return reverse('delivery_dashboard')
            else:
                return reverse('order_tracking', kwargs={'order_id': self.order.order_id})
        
        # Priority 2: Custom Request links
        if "custom_request" in self.notification_type:
            if self.user.profile.role == 'baker':
                return reverse('baker_custom_requests')
            else:
                return reverse('my_custom_requests')
        
        # Priority 3: Fallback based on role
        if self.user.profile.role == 'baker':
            return reverse('baker_dashboard')
        elif self.user.profile.role == 'customer':
            return reverse('my_orders')
        
        return reverse('notifications')

    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"


# Audit Log Model (for admin action logging)
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('suspend', 'Suspend'),
        ('unsuspend', 'Unsuspend'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.action} - {self.model_name}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"





# OTP Model for phone verification
class OTP(models.Model):
    phone_number = models.CharField(max_length=15)
    otp_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"OTP for {self.phone_number}"
    
    def is_expired(self):
        """Check if OTP is expired"""
        return timezone.now() > self.expires_at
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"


# Custom Cake Request Model (handles both AI designs and Photo uploads)
class CustomCakeRequest(models.Model):
    REQUEST_TYPES = [
        ('AI', 'AI Designed'),
        ('PHOTO', 'Photo Reference'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_cake_requests')
    baker = models.ForeignKey('BakerProfile', on_delete=models.SET_NULL, null=True, related_name='received_requests')
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPES)
    
    # Common fields
    reference_image = models.ImageField(upload_to='custom_requests/', blank=True, null=True) 
    description = models.TextField()
    flavor = models.CharField(max_length=100, blank=True, null=True)
    size = models.CharField(max_length=100, blank=True, null=True)
    delivery_date = models.DateField(blank=True, null=True)
    
    # Detailed specs stored as JSON (useful for AI attributes)
    specs = models.JSONField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    price_quote = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    baker_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.request_type} Request - {self.customer.username} -> {self.baker.shop_name if self.baker else 'No Baker'}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Custom Cake Request"
        verbose_name_plural = "Custom Cake Requests"


# Support Ticket Model (for Services)
class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('resolved', 'Resolved'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    resolution_message = models.TextField(blank=True, null=True, help_text="Optional message from admin when resolving")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject} ({self.get_status_display()})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Support Ticket"
        verbose_name_plural = "Support Tickets"


# Website Review Model (for Services)
class WebsiteReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='website_reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.rating} Stars"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Website Review"
        verbose_name_plural = "Website Reviews"


# Coupon Model
class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percent', 'Percentage (%)'),
        ('flat', 'Flat Amount (₹)'),
    ]

    code = models.CharField(max_length=30, unique=True, help_text="Uppercase coupon code e.g. SAVE10")
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percent')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Discount value (% or ₹)")
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Minimum cart total to apply coupon")
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Cap for percentage discounts (optional)")
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True, help_text="Leave blank for no expiry")
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Max total uses; blank = unlimited")
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

    def is_valid(self, order_amount):
        """Check if coupon is valid for the given order amount."""
        now = timezone.now()
        if not self.is_active:
            return False, "This coupon is inactive."
        if now < self.valid_from:
            return False, "This coupon is not yet active."
        if self.valid_until and now > self.valid_until:
            return False, "This coupon has expired."
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False, "This coupon has reached its usage limit."
        if order_amount < self.min_order_amount:
            return False, f"Minimum order amount of ₹{self.min_order_amount} required."
        return True, "Valid"

    def get_discount_amount(self, order_amount):
        """Calculate actual discount amount for the given order total."""
        if self.discount_type == 'percent':
            discount = order_amount * (self.discount_value / Decimal('100'))
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        else:
            discount = min(self.discount_value, order_amount)
        return discount.quantize(Decimal('0.01'))

    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"


# Newsletter Subscriber Model
class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"


# Letter Model (Admin Announcements)
class Letter(models.Model):
    subject = models.CharField(max_length=200)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = "Admin Letter"
        verbose_name_plural = "Admin Letters"
        ordering = ['-sent_at']

