"""
Authentication Views with Enhanced Security
Includes: Login with account lock, Email OTP verification, Role-based access
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.conf import settings
from datetime import timedelta
import random
import uuid

from .models import UserProfile, AuditLog, BakerProfile, Order, Notification, Wallet
from django.db.models import Sum
from decimal import Decimal
from .forms import (
    PasswordLoginForm, RegistrationForm, BakerRegistrationForm, UserProfileForm, 
    BakerProfileForm, CustomPasswordChangeForm
)
from .utils import (
    send_otp_email, send_delivery_thank_you_email, 
    send_order_placed_email, send_baker_delivery_notification_email
)
from django.utils import timezone
from django.db import transaction


logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_audit(user, action, model_name, object_id, description, request=None):
    """Log admin/user actions"""
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        description=description,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:200] if request else ''
    )


from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def login_view(request):
    """Enhanced login view with account lock"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = PasswordLoginForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']
            
            # Try to get user by phone number (which is the username)
            user = authenticate(request, username=phone_number, password=password)
            
            if user is not None:
                # Check account lock/suspension via profile
                try:
                    profile = user.profile
                    if profile.is_account_locked():
                        messages.error(request, 'Account is locked. Please try again later.')
                        log_audit(user, 'login', 'User', user.id, 'Failed login - Account locked', request)
                        return render(request, 'login.html', {'form': form})
                    
                    if profile.is_suspended:
                        messages.error(request, 'Your account has been suspended. Contact admin.')
                        return render(request, 'login.html', {'form': form})
                    
                    profile.reset_failed_attempts()
                except UserProfile.DoesNotExist:
                    pass
                
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                log_audit(user, 'login', 'User', user.id, 'Successful login', request)
                
                # Redirect based on role
                next_url = request.GET.get('next', None)
                if next_url:
                    return redirect(next_url)
                
                try:
                    if user.profile.role == 'baker':
                        return redirect('baker_dashboard')
                    elif user.profile.role == 'delivery_assistant':
                        return redirect('delivery_dashboard')
                    elif user.is_staff:
                        return redirect('admin_dashboard')
                    elif user.profile.role == 'customer':
                        return redirect('customer_home')
                except UserProfile.DoesNotExist:
                    pass
                
                return redirect('home')
            else:
                # Handle failed login
                try:
                    user_obj = User.objects.get(username=phone_number)
                    try:
                        profile = user_obj.profile
                        profile.increment_failed_attempts()
                        remaining = 5 - profile.failed_login_attempts
                        if remaining > 0:
                            messages.error(request, f'Invalid credentials. {remaining} attempts remaining.')
                        else:
                            messages.error(request, 'Account locked after 5 failed attempts.')
                    except UserProfile.DoesNotExist:
                            messages.error(request, 'Invalid phone number or password.')
                    log_audit(user_obj, 'login', 'User', user_obj.id, 'Failed login - Invalid credentials', request)
                except User.DoesNotExist:
                    messages.error(request, 'Invalid phone number or password.')
    else:
        form = PasswordLoginForm()
    
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Logout view"""
    if request.user.is_authenticated:
        log_audit(request.user, 'logout', 'User', request.user.id, 'User logged out', request)
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@ensure_csrf_cookie
@transaction.atomic
def register(request):
    """
    Registration view with email OTP verification.
    - Creates user with is_active=False
    - Sends OTP to user's email
    - Stores email in session for OTP verification page
    - Redirects to verify_otp
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        role = request.POST.get('role', 'customer')
        print(f"DEBUG: Role selected: {role}")
        print(f"DEBUG: POST data: {request.POST}")

        if role == 'baker':
            form = BakerRegistrationForm(request.POST, request.FILES)
            print("DEBUG: Using BakerRegistrationForm")
        else:
            form = RegistrationForm(request.POST)
            print("DEBUG: Using RegistrationForm")

        if form.is_valid():
            print("DEBUG: Form is valid")
            # Create user with phone number as username
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            user = User.objects.create_user(
                username=phone_number,
                email=email, 
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data.get('full_name', ''),
                is_active=False, # Wait for OTP
            )

            # Generate OTP
            otp = str(random.randint(100000, 999999))
            
            # Create user profile
            profile = UserProfile.objects.create(
                user=user,
                phone_number=phone_number,
                secondary_phone_number=form.cleaned_data.get('secondary_phone_number', ''),
                role=form.cleaned_data['role'],
                is_phone_verified=False,
                email_otp=otp,
                otp_expiry=timezone.now() + timedelta(minutes=5)
            )

            # Store phone in session for verification
            request.session['verify_phone'] = phone_number
            request.session['verify_type'] = 'registration'

            # Send OTP
            sent = send_otp_email(email, otp, purpose="registration")
            if not sent:
                messages.warning(request, "Registration successful, but we couldn't send the verification email. Please check the server logs or try resending.")
            else:
                messages.success(request, "OTP has been sent to your email. Please verify to complete registration.")

            # Create baker profile if baker
            if role == 'baker':
                try:
                    BakerProfile.objects.create(
                        user_profile=profile,
                        shop_name=form.cleaned_data['shop_name'],
                        address=form.cleaned_data['address'],
                        city=form.cleaned_data['city'],
                        pincode=form.cleaned_data['pincode'],
                        license_number=form.cleaned_data.get('license_number', ''),
                        fssai_certificate=form.cleaned_data.get('fssai_certificate'),
                        status='pending',
                    )
                    # print("DEBUG: BakerProfile created")
                except Exception as e:
                    # print(f"DEBUG: Error creating BakerProfile: {e}")
                    pass

            # Redirect to OTP verification
            return redirect('verify_otp')
        else:
            print(f"DEBUG: Form errors: {form.errors}")
            messages.error(request, "Please correct the errors below.")
    else:
        # Use BakerRegistrationForm for GET so all fields (including baker ones) are rendered
        # Hidden by JS initially for non-bakers
        form = BakerRegistrationForm()

    return render(request, 'register.html', {'form': form})


@login_required
def profile(request):
    """
    Profile view for viewing and editing user details.
    Handles both Customer and Baker profiles.
    """
    user = request.user
    
    # Get user profile safely
    try:
        user_profile = user.profile
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist (should exist on registration but just in case)
        user_profile = UserProfile.objects.create(user=user, phone_number=user.username)

    # Check if user is a baker
    is_baker = user_profile.role == 'baker'
    baker_profile = None
    if is_baker:
        try:
            baker_profile = user_profile.baker_profile
        except BakerProfile.DoesNotExist:
            pass

    # Calculate Total Revenue (Lifetime)
    calculated_total_revenue = Decimal('0.00')
    if is_baker:
        calculated_total_revenue = Order.objects.filter(
            items__cake__baker=user,
            payment_status='paid'
        ).aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')

    if request.method == 'POST':
        # Default forms
        user_form = UserProfileForm(request.POST, request.FILES, instance=user)
        baker_form = None

        if is_baker and baker_profile:
            baker_form = BakerProfileForm(request.POST, request.FILES, instance=baker_profile)
        
        # Validation
        valid = user_form.is_valid()
        if baker_form:
            valid = valid and baker_form.is_valid()
        
        print(f"DEBUG: request.FILES: {request.FILES.keys()}")
        print(f"DEBUG: user_form valid: {user_form.is_valid()}")
        if not user_form.is_valid():
             print(f"DEBUG: user_form errors: {user_form.errors}")
        
        if valid:
            user_form.save()
            
            # Explicitly handle profile picture upload to ensure it's saved
            if 'profile_picture' in request.FILES:
                profile = user.profile
                profile.profile_picture = request.FILES['profile_picture']
                profile.save()
                
            if baker_form:
                baker_form.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Initial forms
        user_form = UserProfileForm(instance=user)
        baker_form = None
        if is_baker and baker_profile:
            baker_form = BakerProfileForm(instance=baker_profile)
    
    context = {
        'user_form': user_form,
        'baker_form': baker_form,
        'is_baker': is_baker,
        'baker_form': baker_form,
        'is_baker': is_baker,
        'baker_profile': baker_profile, # For read-only fields display
        'total_revenue': calculated_total_revenue,
    }
    return render(request, 'profile.html', context)


@login_required
def remove_profile_picture(request):
    """Remove user's profile picture"""
    try:
        user_profile = request.user.profile
        if user_profile.profile_picture:
            user_profile.profile_picture.delete(save=False)
            user_profile.profile_picture = None
            user_profile.save()
            messages.success(request, "Profile picture removed.")
    except UserProfile.DoesNotExist:
        pass
    
    return redirect('profile')

@ensure_csrf_cookie
def verify_otp(request):
    """Verify registration or login OTP"""
    phone = request.session.get('verify_phone')
    verify_type = request.session.get('verify_type', 'registration')
    
    if not phone:
        messages.error(request, "Session expired. Please try again.")
        return redirect('login')
        
    if request.method == 'POST':
        otp_received = request.POST.get('otp')
        try:
            user = User.objects.get(username=phone)
            profile = user.profile
            
            if profile.email_otp == otp_received and timezone.now() < profile.otp_expiry:
                # Success
                profile.email_otp = None
                profile.otp_expiry = None
                profile.is_phone_verified = True # Mark as verified
                profile.save()
                
                if verify_type == 'registration':
                    user.is_active = True
                    user.save()
                    log_audit(user, 'verify', 'User', user.id, 'User email/phone verified via OTP', request)
                    
                    # Notify Admins about new user
                    admins = User.objects.filter(is_staff=True)
                    role_display = profile.get_role_display()
                    for admin in admins:
                        Notification.objects.create(
                            user=admin,
                            notification_type='order_placed', # Using existing generic type or create new? Let's use 'order_placed' or just a custom string if choices allow
                            title='New User Joined',
                            message=f"A new {role_display}, {user.get_full_name() or user.username}, has joined the system."
                        )
                
                login(request, user)
                messages.success(request, f"Welcome, {user.first_name or user.username}!")
                
                # Cleanup session
                if 'verify_phone' in request.session: del request.session['verify_phone']
                if 'verify_type' in request.session: del request.session['verify_type']
                
                if user.is_staff:
                    return redirect('admin_dashboard')
                if user.profile.role == 'baker':
                    return redirect('baker_dashboard')
                if user.profile.role == 'delivery_assistant':
                    return redirect('delivery_dashboard')
                if user.profile.role == 'customer':
                    return redirect('customer_home')
                return redirect('home')
            else:
                messages.error(request, "Invalid or expired OTP.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('register')
            
    return render(request, 'verify_otp.html', {'phone': phone, 'type': verify_type})

def resend_otp(request):
    """Resend OTP to user's email"""
    phone = request.session.get('verify_phone')
    if not phone:
        return JsonResponse({'status': 'error', 'message': 'Session expired'}, status=400)
        
    try:
        user = User.objects.get(username=phone)
        profile = user.profile
        otp = str(random.randint(100000, 999999))
        profile.email_otp = otp
        profile.otp_expiry = timezone.now() + timedelta(minutes=5)
        profile.save()
        
        send_otp_email(user.email, otp, purpose=request.session.get('verify_type', 'registration'))
        return JsonResponse({'status': 'success', 'message': 'New OTP sent to your email.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def send_login_otp(request):
    """AJAX view to send OTP for login"""
    if request.method == 'POST':
        phone = request.POST.get('phone_number')
        try:
            user = User.objects.get(username=phone)
            # Check if user is active
            if not user.is_active:
                return JsonResponse({'status': 'error', 'message': 'Account is not verified. Please register or verify your email.'})
                
            profile = user.profile
            otp = str(random.randint(100000, 999999))
            profile.email_otp = otp
            profile.otp_expiry = timezone.now() + timedelta(minutes=5)
            profile.save()
            
            # Store in session for verification
            request.session['verify_phone'] = phone
            request.session['verify_type'] = 'login'
            
            sent = send_otp_email(user.email, otp, purpose="login")
            if sent:
                return JsonResponse({'status': 'success', 'message': f'OTP sent to {user.email[:3]}...{user.email[-4:]}'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Failed to send OTP email. Please try again later.'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Phone number not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})






@login_required
def delete_account(request):
    """
    Delete the user's account and related profile.
    Only allowed for customers and bakers.
    """
    if request.method == 'POST':
        user = request.user
        
        # Security: Do not allow admin to delete account via this view
        if user.is_staff or user.profile.role == 'admin':
            messages.error(request, "Administrators cannot delete their accounts via this option.")
            return redirect('profile')
            
        # Log the action before deletion
        log_audit(
            user=user,
            action='DELETE',
            model_name='User',
            object_id=user.id,
            description=f"User {user.username} deleted their own account.",
            request=request
        )
        
        # Soft delete instead of hard delete to preserve order history for bakers
        # Anonymize data to allow the user to re-register with the same phone/email
        suffix = uuid.uuid4().hex[:8]
        user.is_active = False
        user.username = f"del_{suffix}"[:150]
        user.email = ""
        user.save()
        
        # Free up the phone number (must be unique)
        profile = user.profile
        profile.phone_number = str(uuid.uuid4().int)[:15]  # Random 15-digit string to satisfy length limit
        profile.save()
        
        # Logout is implicit on user deletion in many sessions, but good to be explicit
        logout(request)
        
        messages.success(request, "Your account has been successfully deleted. We're sorry to see you go.")
        return redirect('home')
        
    return redirect('profile')

from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def ajax_verify_fssai(request):
    """
    AJAX view to verify FSSAI certificate against entered license number.
    Returns JSON status and message.
    """
    try:
        if request.method == 'POST':
            license_number = request.POST.get('license_number')
            fssai_certificate = request.FILES.get('fssai_certificate')
            
            if not license_number or not fssai_certificate:
                return JsonResponse({'status': 'error', 'message': 'Please provide both license number and certificate image.'}, status=400)
                
            # Check for uniqueness
            if BakerProfile.objects.filter(license_number=license_number).exists():
                return JsonResponse({'status': 'fail', 'message': 'already synced and verification failed'})

            from .ai_utils import OCRUtility
            ocr_result = OCRUtility.extract_fssai_number(fssai_certificate, target_number=license_number)
            
            print(f"DEBUG: OCR Result: {ocr_result}")
            print(f"DEBUG: Target License: {license_number}")
            
            if ocr_result and ocr_result.get('success'):
                extracted_number = ocr_result.get('code')
                if extracted_number and extracted_number.strip().upper() == license_number.strip().upper():
                    return JsonResponse({'status': 'success', 'message': 'Verification Completed!'})
                else:
                    return JsonResponse({
                        'status': 'fail', 
                        'message': "Verification Failed."
                    })
            else:
                return JsonResponse({
                    'status': 'fail', 
                    'message': "Verification Failed."
                })
                
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
    except Exception as e:
        # Catch unexpected errors to prevent frontend crashing, but return clean message
        return JsonResponse({'status': 'error', 'message': 'Verification Failed. Please try again later.'})



@login_required
def delivery_dashboard(request):
    """Dashboard for Delivery Assistant"""
    if request.user.profile.role != 'delivery_assistant':
        messages.warning(request, 'Access denied.')
        return redirect('home')
    
    # Show active orders: confirmed, baking, packing, or out for delivery
    active_orders = Order.objects.filter(
        status__in=['confirmed', 'baking', 'packing', 'out_for_delivery']
    ).order_by('-created_at')
    
    # Show past orders: delivered (limit to recent 20)
    delivered_orders = Order.objects.filter(
        status='delivered'
    ).order_by('-delivered_at')[:20]
    
    context = {
        'active_orders': active_orders,
        'delivered_orders': delivered_orders,
    }
    return render(request, 'delivery_dashboard.html', context)

@login_required
def verify_delivery_otp(request):
    """View for Delivery Assistant to verify the baker-generated OTP"""
    if request.user.profile.role != 'delivery_assistant':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
        
    if request.method == 'POST':
        order_id = request.POST.get('order_id', '')
        otp = request.POST.get('otp', '')
        
        if not order_id:
            return JsonResponse({'status': 'error', 'message': 'Order ID missing'}, status=400)

        # Normalize order_id if needed
        search_id = order_id.strip() if order_id.strip().startswith('#') else f'#{order_id.strip()}'
        order = get_object_or_404(Order, order_id=search_id)

        # If already delivered, just return success (to avoid confusion on double clicks)
        if order.status == 'delivered':
            return JsonResponse({'status': 'success', 'message': 'Delivery already completed.'})

        # Canonicalize OTPs for comparison
        clean_input = str(otp).strip().upper() if otp else ''
        clean_stored = str(order.delivery_otp).strip().upper() if order.delivery_otp else ''

        if clean_input and clean_stored and clean_input == clean_stored:
            order.status = 'delivered'
            order.delivered_at = timezone.now()
            order.otp_verified = True
            order.delivery_otp = None # Clear OTP for security
            order.save()
            
            # 1. Credit Delivery Assistant (request.user)
            if order.delivery_charge > 0:
                Wallet.add_transaction(
                    user=request.user,
                    transaction_type='credit',
                    amount=order.delivery_charge,
                    source='order',
                    description=f'Delivery Fee for Order {order.order_id}',
                    order=order
                )

            # 2. Credit Baker's Wallet and Platform Commission
            baker_items = order.items.filter(cake__baker__isnull=False)
            if baker_items.exists():
                # Assuming one baker per order for payout logic
                baker = baker_items.first().cake.baker
                baker_revenue = sum(item.subtotal for item in baker_items)
                
                try:
                    baker_profile = baker.profile.baker_profile
                    commission_rate = baker_profile.commission_rate
                except:
                    commission_rate = Decimal('10.00')
                
                baker_revenue = Decimal(str(baker_revenue))
                base_commission = baker_revenue * (commission_rate / Decimal('100.00'))
                baker_payout = baker_revenue - base_commission
                
                # Credit Baker
                Wallet.add_transaction(
                    user=baker,
                    transaction_type='credit',
                    amount=baker_payout,
                    source='order',
                    description=f'Payout for Order {order.order_id} (Subtotal: ₹{baker_revenue}, Comm: {commission_rate}%)',
                    order=order
                )
                
                # Platform Commission is base commission MINUS coupon discount
                # This ensures the baker gets their full share and admin pays for the discount
                net_commission = base_commission - order.coupon_discount
                
                # Credit/Debit Commission to Admin
                admin_profile = UserProfile.objects.filter(role='admin').first()
                if admin_profile:
                    if net_commission > 0:
                        Wallet.add_transaction(
                            user=admin_profile.user,
                            transaction_type='credit',
                            amount=net_commission,
                            source='commission',
                            description=f'Platform Commission from Order {order.order_id} (Net after ₹{order.coupon_discount} discount)',
                            order=order
                        )
                    elif net_commission < 0:
                        # Admin covers the excess discount from their own wallet
                        Wallet.add_transaction(
                            user=admin_profile.user,
                            transaction_type='debit',
                            amount=abs(net_commission),
                            source='commission',
                            description=f'Platform Loss due to Coupon on Order {order.order_id} (Net after ₹{order.coupon_discount} discount)',
                            order=order
                        )

                # 3. Notify Baker via App and Email
                Notification.objects.create(
                    user=baker,
                    notification_type='order_delivered',
                    title='Delivery Completed',
                    message=f'Order {order.order_id} has been delivered. ₹{baker_payout} credited to your wallet.',
                    order=order
                )
                
                try:
                    shop_name = baker.profile.baker_profile.shop_name
                except:
                    shop_name = baker.username

                send_baker_delivery_notification_email(
                    email=baker.email,
                    order_id=order.order_id,
                    baker_shop_name=shop_name,
                    payout_amount=baker_payout
                )
            
            Notification.objects.create(
                user=order.customer,
                notification_type='order_delivered',
                title='Order Delivered',
                message=f'Your order {order.order_id} has been delivered by our assistant.',
                order=order
            )
            
            # Send thank you email to customer
            send_delivery_thank_you_email(
                email=order.customer.email,
                order_id=order.order_id,
                customer_name=order.customer.get_full_name() or order.customer.username
            )
            
            return JsonResponse({'status': 'success', 'message': 'Delivery verified and completed!'})
        else:
            return JsonResponse({'status': 'fail', 'message': 'Invalid OTP. Please check with the baker.'})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
def change_password(request):
    """View for all users to change their password"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'change_password.html', {
        'form': form
    })
