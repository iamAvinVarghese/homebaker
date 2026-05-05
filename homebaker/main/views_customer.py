"""
Customer Module Views
Includes: Home, Cake listing, Cart, Order placement, Tracking, Reviews, Wallet
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.utils import timezone
from .utils import (
    send_otp_email, send_delivery_thank_you_email, send_order_placed_email,
    send_baker_new_order_email, send_baker_order_cancelled_email, send_baker_custom_request_email,
    send_baker_review_email
)
from datetime import date, timedelta, datetime
from decimal import Decimal
from .models import (
    Cake, Order, OrderItem, UserProfile, Review, Wallet, Notification,
    CakeSize, CustomCakeRequest, BakerProfile, Coupon, NewsletterSubscriber
)
from .forms import CakeSearchForm, ReviewForm, WalletRechargeForm, WalletWithdrawForm
from .ai_utils import RecommendationEngine
from . import ml_pricing


def subscribe_newsletter(request):
    """AJAX view to subscribe to the newsletter/letterbox"""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
            if created:
                return JsonResponse({'status': 'success', 'message': 'Successfully subscribed to the Letterbox! 💌'})
            else:
                return JsonResponse({'status': 'info', 'message': 'You are already on our sweet list! ✨'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


@ensure_csrf_cookie
def home(request):
    """Home page with featured cakes and recommendations"""
    # Redirect authenticated customers to their dedicated home page
    if request.user.is_authenticated:
        try:
            role = request.user.profile.role
            if role == 'customer':
                return redirect('customer_home')
            elif role == 'baker':
                return redirect('baker_dashboard')
            elif role == 'delivery_assistant':
                return redirect('delivery_dashboard')
            elif request.user.is_staff:
                return redirect('admin_dashboard')
        except:
            pass
        return redirect('cakes')

    featured_cakes = Cake.objects.filter(
        is_available=True,
        baker__profile__baker_profile__status='approved'
    ).order_by('-average_rating', '-order_count')[:6]
    
    # Trending cakes
    trending_cakes = RecommendationEngine.get_trending_cakes(limit=4)
    
    # Platform Statistics
    total_customers = UserProfile.objects.filter(role='customer').count()
    total_bakers = BakerProfile.objects.filter(status='approved').count()
    cakes_delivered = Order.objects.filter(status='delivered').count()
    
    # Website Reviews for Testimonials
    from .models import WebsiteReview
    website_reviews = WebsiteReview.objects.filter(is_approved=True).order_by('-rating', '-created_at')[:3]
    
    context = {
        'featured_cakes': featured_cakes,
        'trending_cakes': trending_cakes,
        'total_customers': total_customers,
        'total_bakers': total_bakers,
        'cakes_delivered': cakes_delivered,
        'website_reviews': website_reviews,
    }
    return render(request, 'home.html', context)


def about_us(request):
    """About Us page"""
    return render(request, 'about_us.html')


def faq(request):
    """FAQ page"""
    return render(request, 'faq.html')



@ensure_csrf_cookie
@login_required
def customer_home(request):
    """Personalized home page for logged-in customers"""
    # Only allow customers
    try:
        if request.user.profile.role != 'customer':
            return redirect('home')
    except:
        pass

    user = request.user

    # Recent orders
    recent_orders = Order.objects.filter(
        customer=user
    ).order_by('-created_at')[:5]

    # Order stats
    all_orders = Order.objects.filter(customer=user)
    total_orders = all_orders.count()
    active_orders = all_orders.filter(
        status__in=['pending', 'confirmed', 'baking', 'packing', 'out_for_delivery']
    ).count()
    delivered_orders = all_orders.filter(status='delivered').count()

    # Wallet balance
    wallet_balance = Wallet.get_user_balance(user)

    # Recommended / trending cakes
    try:
        recommended_cakes = RecommendationEngine.get_recommendations_for_user(user, limit=4)
    except:
        recommended_cakes = []

    trending_cakes = RecommendationEngine.get_trending_cakes(limit=4)

    # Unread notifications count (already available via context processor, but grab explicitly too)
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()

    context = {
        'user': user,
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'active_orders': active_orders,
        'delivered_orders': delivered_orders,
        'wallet_balance': wallet_balance,
        'recommended_cakes': recommended_cakes,
        'trending_cakes': trending_cakes,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'customer_home.html', context)


def cake_list(request):
    """Cake listing with search and filters"""
    # Only show cakes from approved bakers
    cakes = Cake.objects.filter(
        is_available=True, 
        baker__profile__baker_profile__status='approved'
    )
    form = CakeSearchForm(request.GET)
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        flavor = form.cleaned_data.get('flavor')
        occasion = form.cleaned_data.get('occasion')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        
        if query:
            cakes = cakes.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        
        if flavor:
            cakes = cakes.filter(flavor=flavor)
        
        if occasion:
            cakes = cakes.filter(occasion=occasion)
        
        if min_price:
            cakes = cakes.filter(price__gte=min_price)
        
        if max_price:
            cakes = cakes.filter(price__lte=max_price)
            
        top_rated = form.cleaned_data.get('top_rated')
        if top_rated:
            # Filter by Baker's rating as per request "top rated bakers"
            cakes = cakes.filter(baker__profile__baker_profile__average_rating__gte=4.0)
            
        sort_by = form.cleaned_data.get('sort_by')
        if sort_by == 'price_asc':
            cakes = cakes.order_by('price')
        elif sort_by == 'price_desc':
            cakes = cakes.order_by('-price')
        elif sort_by == 'rating':
            cakes = cakes.order_by('-average_rating')
        elif sort_by == 'newest':
            cakes = cakes.order_by('-created_at')
        else:
            # Default sort
            cakes = cakes.order_by('-created_at')
    
    # Increment view count for each cake
    for cake in cakes:
        cake.increment_views()
    
    context = {
        'cakes': cakes,
        'form': form,
    }
    return render(request, 'cake_list.html', context)


@login_required
def add_to_cart(request, cake_id):
    """Add cake to cart (session-based)"""
    # Restrict Bakers and Admins from purchasing
    if request.user.profile.role in ['baker', 'admin']:
        messages.error(request, "Bakers and Admins cannot purchase cakes. This option is only for Customers.")
        return redirect('cakes')

    cake = get_object_or_404(Cake, id=cake_id, is_available=True)
    
    cart = request.session.get('cart', {})
    cake_key = str(cake_id)
    
    if cake_key in cart:
        cart[cake_key]['quantity'] += 1
    else:
        cart[cake_key] = {
            'cake_id': cake.id,
            'name': cake.name,
            'price': float(cake.price),
            'quantity': 1,
            'image_url': cake.image.url if cake.image else (cake.image_url or ''),
        }
    
    request.session['cart'] = cart
    messages.success(request, f'{cake.name} added to cart!')
    
    return redirect('cakes')


@login_required
def cart(request):
    """View standard cart"""
    cart = request.session.get('cart', {})
    cart_items = []
    total = Decimal('0.00')

    for key, item in cart.items():
        try:
            cake = Cake.objects.get(id=item['cake_id'])
            weight = float(item['quantity'])
            base_price = Decimal(str(item['price']))

            # ML-adjusted price
            adjusted_price, ml_multiplier = ml_pricing.get_adjusted_price(
                base_price_per_kg=base_price,
                weight=weight,
                flavor=cake.flavor,
                occasion=cake.occasion,
                has_message=bool(item.get('message_on_cake', '')),
                is_custom=False,
            )

            # Store the adjusted price back into session for checkout to use
            cart[key]['ml_price'] = str(adjusted_price)

            item_total = adjusted_price * Decimal(str(weight))
            total += item_total

            cart_items.append({
                'cart_key': key,
                'cake': cake,
                'quantity': weight,
                'base_price': base_price,
                'adjusted_price': adjusted_price,
                'ml_multiplier': round(ml_multiplier, 2),
                'total': item_total,
            })
        except Cake.DoesNotExist:
            continue

    request.session['cart'] = cart  # persist ml_price adjustments
    delivery_charge = Decimal('50.00')
    grand_total = total + delivery_charge

    context = {
        'cart_items': cart_items,
        'subtotal': total,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total,
    }
    return render(request, 'cart.html', context)


@login_required
def custom_cart(request):
    """View specialized custom cart"""
    custom_cart = request.session.get('custom_cart', {})
    cart_items = []
    total = Decimal('0.00')
    
    for key, item in custom_cart.items():
        try:
            cake = Cake.objects.get(id=item['cake_id'])
            item_total = Decimal(str(item['price'])) * Decimal(str(item['quantity']))
            total += item_total
            
            cart_items.append({
                'cake': cake,
                'quantity': item['quantity'],
                'price': item['price'],
                'total': item_total,
                'is_custom': True,
                'custom_size': item.get('custom_size', 'Standard'),
            })
        except Cake.DoesNotExist:
            continue
    
    delivery_charge = Decimal('50.00')
    grand_total = total + delivery_charge
    
    context = {
        'cart_items': cart_items,
        'subtotal': total,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total,
    }
    return render(request, 'custom_cart.html', context)


@login_required
def remove_from_cart(request, cake_id):
    """Remove cake from cart"""
    cart = request.session.get('cart', {})
    cake_key = str(cake_id)
    
    if cake_key in cart:
        name = cart[cake_key]['name']
        del cart[cake_key]
        request.session['cart'] = cart
        messages.success(request, f'{name} removed from cart.')
    
    return redirect('cart')

@login_required
def update_cart(request, cake_id):
    """Update cake quantity/size in cart"""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        cake_key = str(cake_id)
        
        try:
            quantity = float(request.POST.get('quantity', 1))
            if quantity in [0.5, 1.0, 2.0, 3.0]:
                if cake_key in cart:
                    cart[cake_key]['quantity'] = quantity
                    request.session['cart'] = cart
                    messages.success(request, f'Updated {cart[cake_key]["name"]} size to {quantity} kg.')
            else:
                messages.error(request, 'Size must be 0.5, 1, 2, or 3 kg.')
        except ValueError:
            messages.error(request, 'Invalid size selected.')
            
    return redirect('cart')

@login_required
def checkout(request):
    """Checkout and create order"""
    # Restrict Bakers and Admins from purchasing
    if request.user.profile.role in ['baker', 'admin']:
        messages.error(request, "Bakers and Admins cannot purchase cakes. This option is only for Customers.")
        return redirect('cakes')

    cart_type = request.GET.get('cart_type', 'standard')
    if request.method == 'POST':
        cart_type = request.POST.get('cart_type', 'standard')
    
    session_key = 'custom_cart' if cart_type == 'custom' else 'cart'
    cart = request.session.get(session_key, {})
    
    # Filter by selected items if provided
    selected_str = request.GET.get('selected', '')
    selected_ids = [s for s in selected_str.split(',') if s]
    
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cakes')
    
    if request.method == 'POST':
        address_option = request.POST.get('address_option')
        payment_method = request.POST.get('payment_method', 'wallet')
        
        # Determine delivery address
        delivery_address = ''
        if address_option == 'saved':
            try:
                delivery_address = request.user.profile.default_address
            except UserProfile.DoesNotExist:
                delivery_address = ''
        else:
            delivery_address = request.POST.get('new_address')
            save_as_default = request.POST.get('save_as_default')
            
            # Update default address if requested
            if save_as_default and delivery_address:
                try:
                    profile = request.user.profile
                    profile.default_address = delivery_address
                    profile.save()
                except UserProfile.DoesNotExist:
                    # Create profile if it doesn't exist
                    UserProfile.objects.create(user=request.user, default_address=delivery_address)


        delivery_date_str = request.POST.get('delivery_date')
        
        if not delivery_date_str or not delivery_address:
            messages.error(request, 'Please provide delivery date and address.')
            return redirect(f"{request.path}?selected={selected_str}&cart_type={cart_type}")
        
        try:
            delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid delivery date format.')
            return redirect(f"{request.path}?selected={selected_str}&cart_type={cart_type}")
        
        # Calculate totals for selected items only
        subtotal = Decimal('0.00')
        final_items_to_order = []
        for cake_id, item in cart.items():
            if not selected_ids or cake_id in selected_ids:
                # Use ML-adjusted price if available, otherwise fall back to base price
                price_to_use = item.get('ml_price') or item['price']
                subtotal += Decimal(str(price_to_use)) * Decimal(str(item['quantity']))
                final_items_to_order.append({**item, 'price': price_to_use})
        
        if not final_items_to_order:
            messages.error(request, 'No items selected for checkout.')
            return redirect('cart')
        
        delivery_charge = Decimal('50.00')
        total_amount = subtotal + delivery_charge

        # --- Coupon ---
        coupon_code = request.POST.get('coupon_code', '').strip().upper()
        coupon_discount = Decimal('0.00')
        applied_coupon = None
        if coupon_code:
            try:
                applied_coupon = Coupon.objects.get(code=coupon_code)
                is_valid, msg = applied_coupon.is_valid(subtotal)
                if is_valid:
                    coupon_discount = applied_coupon.get_discount_amount(subtotal)
                    total_amount = max(total_amount - coupon_discount, Decimal('0.00'))
                else:
                    messages.warning(request, f'Coupon not applied: {msg}')
                    applied_coupon = None
            except Coupon.DoesNotExist:
                messages.warning(request, 'Invalid coupon code.')

        # Check wallet balance if paying with wallet
        if payment_method == 'wallet':
            wallet_balance = Wallet.get_user_balance(request.user)
            
            if wallet_balance < total_amount:
                messages.error(request, f'Insufficient wallet balance. Required: ₹{total_amount}, Available: ₹{wallet_balance}')
                return redirect(f"{request.path}?cart_type={cart_type}")
        
        # Create order within a transaction or with error handling
        try:
            order = Order.objects.create(
                customer=request.user,
                delivery_date=delivery_date,
                delivery_address=delivery_address,
                delivery_charge=delivery_charge,
                subtotal=subtotal,
                coupon_discount=coupon_discount,
                total_amount=total_amount,
                payment_method=payment_method,
                status='pending',
                payment_status='pending'
            )
            
            # Create order items
            for item in final_items_to_order:
                try:
                    cake = Cake.objects.get(id=item['cake_id'])
                    quantity = Decimal(str(item['quantity']))
                    unit_price = Decimal(str(item['price']))
                    
                    OrderItem.objects.create(
                        order=order,
                        cake=cake,
                        quantity=quantity,
                        unit_price=unit_price,
                        subtotal=unit_price * Decimal(str(quantity)),
                        message_on_cake=item.get('message_on_cake', '')
                    )
                    
                    cake.increment_orders()
                except Cake.DoesNotExist:
                    # If a cake vanished from DB, we might want to fail the whole order
                    order.delete()
                    messages.error(request, 'One or more items in your cart are no longer available.')
                    return redirect('cart')
        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
            return redirect(f"{request.path}?cart_type={cart_type}")
        
        # Process payment
        if payment_method == 'wallet':
            Wallet.add_transaction(
                user=request.user,
                transaction_type='debit',
                amount=order.total_amount,
                source='order',
                description=f'Order {order.order_id}',
                order=order
            )
            order.payment_status = 'paid'

        # Increment coupon usage
        if applied_coupon:
            applied_coupon.used_count += 1
            applied_coupon.save(update_fields=['used_count'])

        order.save()

        # Update CustomCakeRequest status if this was a custom order
        for item in order.items.all():
            if item.cake.name.startswith("Custom Cake Request #"):
                try:
                    request_id_str = item.cake.name.split("#")[-1]
                    request_id = int(request_id_str)
                    from .models import CustomCakeRequest
                    CustomCakeRequest.objects.filter(id=request_id).update(status='COMPLETED')
                except (ValueError, IndexError):
                    pass
        
        # Clear specific cart
        request.session[session_key] = {}
        
        # Create notification for Customer
        Notification.objects.create(
            user=request.user,
            notification_type='order_placed',
            title='Order Placed Successfully',
            message=f'Your order {order.order_id} has been placed successfully.',
            order=order
        )

        # Notify Bakers
        bakers = set()
        for item in order.items.all():
            if item.cake.baker:
                bakers.add(item.cake.baker)
        
        for baker in bakers:
            Notification.objects.create(
                user=baker,
                notification_type='new_order',
                title='New Order Received',
                message=f'You have received a new order {order.order_id}. Please check your dashboard for details.',
                order=order
            )
            try:
                shop_name = baker.profile.baker_profile.shop_name
            except:
                shop_name = baker.username
            send_baker_new_order_email(baker.email, order, shop_name)
        
        # Send Order Confirmation Email
        send_order_placed_email(
            email=request.user.email,
            order=order,
            customer_name=request.user.first_name or request.user.username
        )
        
        messages.success(request, f'Order placed successfully! Order ID: {order.order_id}')
        return redirect('order_tracking', order_id=order.order_id)
    
    # GET request - show checkout form
    cart_items = []
    total = Decimal('0.00')
    
    for cake_id, item in cart.items():
        if not selected_ids or cake_id in selected_ids:
            try:
                cake = Cake.objects.get(id=item['cake_id'])
                item_total = Decimal(str(item['price'])) * Decimal(str(item['quantity']))
                total += item_total
                
                cart_items.append({
                    'cake': cake,
                    'quantity': item['quantity'],
                    'price': item['price'],
                    'total': item_total,
                    'is_custom': item.get('is_custom', False),
                    'custom_size': item.get('custom_size', ''),
                })
            except Cake.DoesNotExist:
                continue
    
    delivery_charge = Decimal('50.00')
    grand_total = total + delivery_charge
    wallet_balance = Wallet.get_user_balance(request.user) if request.user.is_authenticated else Decimal('0.00')
    
    default_address = ''
    if request.user.is_authenticated:
        try:
            default_address = request.user.profile.default_address
        except UserProfile.DoesNotExist:
            pass

    context = {
        'cart_items': cart_items,
        'subtotal': total,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total,
        'wallet_balance': wallet_balance,
        'default_address': default_address,
        'cart_type': cart_type,
    }
    return render(request, 'checkout.html', context)


@login_required
def apply_coupon(request):
    """AJAX endpoint to validate a coupon code and return discount info."""
    if request.method != 'POST':
        return JsonResponse({'valid': False, 'message': 'Invalid request.'})

    code = request.POST.get('coupon_code', '').strip().upper()
    subtotal_str = request.POST.get('subtotal', '0')

    try:
        subtotal = Decimal(subtotal_str)
    except Exception:
        return JsonResponse({'valid': False, 'message': 'Invalid subtotal.'})

    if not code:
        return JsonResponse({'valid': False, 'message': 'Please enter a coupon code.'})

    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        return JsonResponse({'valid': False, 'message': 'Invalid coupon code.'})

    is_valid, msg = coupon.is_valid(subtotal)
    if not is_valid:
        return JsonResponse({'valid': False, 'message': msg})

    discount = coupon.get_discount_amount(subtotal)
    return JsonResponse({
        'valid': True,
        'discount': str(discount),
        'message': f'Coupon applied! You save ₹{discount}.',
    })



@login_required
def order_tracking(request, order_id):
    """Order tracking page - accessible by customer, assigned baker, or admin"""
    # Normalize order_id if passed without # or with whitespace
    clean_url_id = order_id.strip()
    search_id = clean_url_id if clean_url_id.startswith('#') else f'#{clean_url_id}'
    
    # Query using Q objects to allow owner OR assigned baker access
    from django.db.models import Q
    
    order_query = Order.objects.filter(order_id=search_id)
    
    if not request.user.is_staff:
        # Filter for owner OR assigned baker
        order_query = order_query.filter(
            Q(customer=request.user) | Q(items__cake__baker=request.user)
        ).distinct()
    
    # Try search_id first, then fallback to clean_url_id just in case of inconsistency
    order = order_query.first()
    if not order:
        # Fallback to literal URL ID
        fallback_query = Order.objects.filter(order_id=clean_url_id)
        if not request.user.is_staff:
            fallback_query = fallback_query.filter(
                Q(customer=request.user) | Q(items__cake__baker=request.user)
            ).distinct()
        order = fallback_query.first()

    if not order:
        # Final effort: if user is logged in, show their orders for easier debugging if 404 still happens
        return render(request, '404_order.html', {'order_id': order_id}, status=404)
    
    timeline = order.get_status_timeline()
    
    context = {
        'order': order,
        'timeline': timeline,
    }
    return render(request, 'order_tracking_fixed.html', context)


@login_required
def my_orders(request):
    """My orders page"""
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    
    context = {
        'orders': orders
    }
    return render(request, 'my_orders.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read via AJAX"""
    from django.http import JsonResponse
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})


@login_required
def mark_all_notifications_read(request):
    """Mark all unread notifications for the user as read via AJAX"""
    from django.http import JsonResponse
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})


@login_required
def notifications_list(request):
    """Display all notifications for the current user"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Optional: Logic to mark all as read when viewing the page could be added here, 
    # but the user specifically asked for an "option" to mark as read.
    
    context = {
        'notifications_list': notifications,
    }
    return render(request, 'notifications.html', context)


@login_required
def add_review(request, order_id):
    """Add review for delivered order"""
    search_id = order_id if order_id.startswith('#') else f'#{order_id}'
    order = get_object_or_404(Order, order_id=search_id, customer=request.user, status='delivered')
    
    # Check if review already exists
    if hasattr(order, 'review'):
        messages.info(request, 'You have already reviewed this order.')
        return redirect('my_orders')
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            # Get first cake from order
            order_item = order.items.first()
            if order_item:
                review = form.save(commit=False)
                review.order = order
                review.cake = order_item.cake
                review.customer = request.user
                review.save()
                
                messages.success(request, 'Thank you for your review!')
                return redirect('my_orders')
    else:
        form = ReviewForm()
    
    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'add_review.html', context)


@login_required
def wallet(request):
    """Wallet page"""
    wallet_balance = Wallet.get_user_balance(request.user)
    transactions = Wallet.objects.filter(user=request.user).order_by('-created_at')[:20]
    
    recharge_form = WalletRechargeForm()
    withdraw_form = WalletWithdrawForm()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'recharge':
            recharge_form = WalletRechargeForm(request.POST)
            if recharge_form.is_valid():
                amount = recharge_form.cleaned_data['amount']
                Wallet.add_transaction(
                    user=request.user,
                    transaction_type='credit',
                    amount=amount,
                    source='recharge',
                    description='Wallet Recharge'
                )
                messages.success(request, f'₹{amount} added to your wallet!')
                return redirect('wallet')
        
        elif action == 'withdraw':
            # Withdrawal enabled for all roles
                
            withdraw_form = WalletWithdrawForm(request.POST)
            if withdraw_form.is_valid():
                amount = withdraw_form.cleaned_data['amount']
                
                # Check balance
                if amount > wallet_balance:
                    messages.error(request, f'Insufficient balance for withdrawal. Available: ₹{wallet_balance}')
                else:
                    Wallet.add_transaction(
                        user=request.user,
                        transaction_type='debit',
                        amount=amount,
                        source='withdrawal',
                        description='Wallet Withdrawal'
                    )
                    messages.success(request, f'₹{amount} withdrawn successfully!')
                    return redirect('wallet')
    
    context = {
        'wallet_balance': wallet_balance,
        'transactions': transactions,
        'recharge_form': recharge_form,
        'withdraw_form': withdraw_form,
    }
    return render(request, 'wallet.html', context)


@login_required
def cancel_order(request, order_id):
    """Cancel an order if it is pending"""
    order = get_object_or_404(Order, order_id=order_id, customer=request.user)
    
    if order.status != 'pending':
        messages.error(request, 'Only pending orders can be cancelled.')
        return redirect('my_orders')
    
    if request.method == 'POST':
        # Refund to wallet if paid via wallet
        if order.payment_method == 'wallet' and order.payment_status == 'paid':
            Wallet.add_transaction(
                user=request.user,
                transaction_type='credit',
                amount=order.total_amount,
                source='refund',
                description=f'Refund for Order {order.order_id}',
                order=order
            )
            order.payment_status = 'refunded'
            messages.success(request, f'Order cancelled. ₹{order.total_amount} refunded to your wallet.')
        else:
            messages.success(request, 'Order cancelled successfully.')
            
        order.status = 'cancelled'
        order.save()
        
        # Create notification for Customer
        Notification.objects.create(
            user=request.user,
            notification_type='order_cancelled',
            title='Order Cancelled',
            message=f'Your order {order.order_id} has been cancelled.',
            order=order
        )

        # Notify Bakers of Cancellation
        bakers = set()
        for item in order.items.all():
            if item.cake.baker:
                bakers.add(item.cake.baker)
        
        for baker in bakers:
            Notification.objects.create(
                user=baker,
                notification_type='order_cancelled',
                title='Order Cancelled',
                message=f'Order {order.order_id} has been cancelled by the customer.',
                order=order
            )
            try:
                shop_name = baker.profile.baker_profile.shop_name
            except:
                shop_name = baker.username
            send_baker_order_cancelled_email(baker.email, order.order_id, shop_name)
        
        return redirect('my_orders')
    
    return redirect('my_orders')


@login_required
def services_index(request):
    """Services page for support tickets and website reviews."""
    if request.user.is_staff:
        return redirect('admin_helpdesk')
    
    from .forms import SupportTicketForm, WebsiteReviewForm
    from .models import WebsiteReview
    
    ticket_form = SupportTicketForm()
    
    existing_review = WebsiteReview.objects.filter(user=request.user).first()
    review_form = WebsiteReviewForm(instance=existing_review)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'submit_ticket':
            ticket_form = SupportTicketForm(request.POST)
            if ticket_form.is_valid():
                ticket = ticket_form.save(commit=False)
                ticket.user = request.user
                ticket.save()
                messages.success(request, 'Support ticket submitted successfully. Admin will review it shortly.')
                return redirect('services')
                
        elif action == 'submit_review':
            review_form = WebsiteReviewForm(request.POST, instance=existing_review)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.user = request.user
                review.is_approved = True  # Auto-approve for homepage display
                review.save()
                if existing_review:
                    messages.success(request, 'Thank you! Your website review has been updated.')
                else:
                    messages.success(request, 'Thank you! Your website review has been submitted and is featured on the homepage.')
                return redirect('services')
                
    context = {
        'ticket_form': ticket_form,
        'review_form': review_form,
        'has_existing_review': existing_review is not None,
    }
    return render(request, 'services.html', context)


@login_required
def custom_cake(request):
    """AI Custom Cake Design View"""
    from .forms import CustomCakeForm
    from .ai_utils import CakeDesigner
    
    result = None
    
    if request.method == 'POST':
        form = CustomCakeForm(request.POST)
        if form.is_valid():
            # Get requirements
            requirements = {
                'size': form.cleaned_data['size'],
                'shape': form.cleaned_data['shape'],
                'flavor': form.cleaned_data['flavor'],
                'primary_colors': form.cleaned_data['primary_colors'],
                'occasion': form.cleaned_data['occasion'],
                'design_style': form.cleaned_data['design_style'],
                'message_on_cake': form.cleaned_data.get('message_on_cake', ''),
                'extra_instructions': form.cleaned_data.get('extra_instructions', '')
            }
            
            # Call AI
            result = CakeDesigner.generate_custom_design(requirements)
            
            if 'error' in result:
                messages.error(request, result['error'])
            
    else:
        form = CustomCakeForm()
    
    # Fetch bakers who accept custom orders
    from .models import BakerProfile
    bakers = BakerProfile.objects.filter(accepts_custom_orders=True).select_related('user_profile__user')
    
    context = {
        'form': form,
        'result': result,
        'bakers': bakers,
    }
    return render(request, 'custom_cake.html', context)


@login_required
def photo_custom_cake(request):
    """Photo-based Custom Cake Order View"""
    from .forms import PhotoCustomCakeForm
    
    photo_request = None
    
    if request.method == 'POST':
        form = PhotoCustomCakeForm(request.POST, request.FILES)
        if form.is_valid():
            photo_request = form.save(commit=False)
            photo_request.customer = request.user
            photo_request.save()
            messages.success(request, "Image uploaded successfully! Now select a baker to request a quote.")
    else:
        form = PhotoCustomCakeForm()
    
    # Fetch bakers who accept custom orders
    bakers = BakerProfile.objects.filter(accepts_custom_orders=True).select_related('user_profile__user')
    
    context = {
        'form': form,
        'photo_request': photo_request,
        'bakers': bakers,
    }
    return render(request, 'photo_custom_cake.html', context)


@login_required
def my_custom_requests(request):
    """View for customers to track their custom cake requests and quotes"""
    requests = CustomCakeRequest.objects.filter(customer=request.user)
    return render(request, 'customer/custom_requests.html', {'custom_requests': requests})


@login_required
def submit_custom_request(request):
    """View to handle the formal submission of a custom cake request to a baker"""
    if request.method == 'POST':
        baker_id = request.POST.get('baker_id')
        request_type = request.POST.get('request_type') # 'AI' or 'PHOTO'
        description = request.POST.get('description', '')
        flavor = request.POST.get('flavor', '')
        size = request.POST.get('size', '')
        
        baker = get_object_or_404(BakerProfile, id=baker_id)
        
        # Create the request
        custom_request = CustomCakeRequest(
            customer=request.user,
            baker=baker,
            request_type=request_type,
            description=description,
            flavor=flavor,
            size=size,
            status='PENDING'
        )
        
        # Handle Image and Specs
        if request_type == 'AI':
            specs = {
                'image_url': request.POST.get('image_url'),
                'shape': request.POST.get('shape'),
                'occasion': request.POST.get('occasion'),
                'design_style': request.POST.get('design_style'),
                'message_on_cake': request.POST.get('message_on_cake'),
                'extra_instructions': request.POST.get('extra_instructions')
            }
            custom_request.specs = specs
        elif request_type == 'PHOTO':
            photo_req_id = request.POST.get('photo_req_id')
            if photo_req_id:
                custom_request = get_object_or_404(CustomCakeRequest, id=photo_req_id)
                custom_request.baker = baker
                custom_request.status = 'PENDING'
                # Description/flavor might have been updated in the modal form
                custom_request.description = description
                custom_request.flavor = flavor
                custom_request.size = size
                custom_request.save()
                messages.success(request, f"Request sent to {baker.shop_name}!")
                return redirect('my_custom_requests')

        custom_request.save()

        # Notify Baker of New Custom Request
        Notification.objects.create(
            user=baker.user_profile.user,
            notification_type='custom_request_received',
            title='New Custom Request',
            message=f'A customer has submitted a new custom cake request. Please review and provide an offer.',
        )
        
        # Send professional email to baker
        send_baker_custom_request_email(
            email=baker.user_profile.user.email,
            customer_name=request.user.get_full_name() or request.user.username,
            baker_shop_name=baker.shop_name,
            custom_request=custom_request
        )

        messages.success(request, f"Request sent to {baker.shop_name}!")
        return redirect('my_custom_requests')
        
    return redirect('cakes')


@login_required
def cancel_custom_request(request, request_id):
    """Cancel a custom cake request if it is still pending"""
    try:
        custom_request = CustomCakeRequest.objects.get(id=request_id, customer=request.user)
    except CustomCakeRequest.DoesNotExist:
        messages.error(request, "Request not found.")
        return redirect('my_custom_requests')

    if custom_request.status == 'PENDING':
        custom_request.status = 'CANCELLED'
        custom_request.save()
        messages.success(request, "Your custom request has been cancelled.")
    else:
        messages.error(request, "Only pending requests can be cancelled.")
    
    return redirect('my_custom_requests')


@login_required
def finalize_custom_request(request, request_id):
    """Convert an accepted custom request into a cart item"""
    # Restrict Bakers and Admins from purchasing
    if request.user.profile.role in ['baker', 'admin']:
        messages.error(request, "Bakers and Admins cannot purchase cakes. This option is only for Customers.")
        return redirect('my_custom_requests')

    try:
        custom_request = CustomCakeRequest.objects.get(id=request_id, customer=request.user)
    except CustomCakeRequest.DoesNotExist:
        messages.error(request, "Request not found.")
        return redirect('my_custom_requests')

    if custom_request.status != 'ACCEPTED':
        messages.error(request, "Only accepted requests can be finalized.")
        return redirect('my_custom_requests')

    if not custom_request.price_quote or custom_request.price_quote <= 0:
        messages.error(request, "Price not set by baker. Please contact the baker.")
        return redirect('my_custom_requests')
        
    # Check if a cake already exists for this request (to avoid duplicates)
    cake_name = f"Custom Cake Request #{custom_request.id}"
    
    # Create a temporary/hidden Cake object for this order
    cake, created = Cake.objects.get_or_create(
        name=cake_name,
        defaults={
            'flavor': custom_request.flavor or 'Standard', 
            'occasion': 'custom',
            'price': custom_request.price_quote if custom_request.price_quote is not None else 0.00,
            'description': f"Custom Request: {custom_request.description}. Baker Message: {custom_request.baker_message}",
            'is_available': False, # Hidden from public listing
            'baker': custom_request.baker.user_profile.user,
            'image': custom_request.reference_image if custom_request.request_type == 'PHOTO' else None,
            'image_url': custom_request.specs.get('image_url') if custom_request.specs else None 
        }
    )
    
    # If it was already created, update price just in case
    if not created:
        cake.price = custom_request.price_quote if custom_request.price_quote is not None else 0.00
        
        # Ensure image is set if available
        if not cake.image and custom_request.request_type == 'PHOTO':
             cake.image = custom_request.reference_image
        if not cake.image_url and custom_request.specs and 'image_url' in custom_request.specs:
             cake.image_url = custom_request.specs['image_url']
             
        cake.save()
        
    # Add to custom cart (separate from regular cart)
    custom_cart = request.session.get('custom_cart', {})
    cake_key = str(cake.id)
    
    custom_cart[cake_key] = {
        'cake_id': cake.id,
        'name': cake.name,
        'price': float(cake.price),
        'quantity': 1,
        'image_url': cake.image.url if cake.image else (cake.image_url or ''),
        'is_custom': True,
        'custom_size': custom_request.size or 'Standard',
        'message_on_cake': custom_request.specs.get('message_on_cake', '') if custom_request.specs else ''
    }
    
    request.session['custom_cart'] = custom_cart
    messages.success(request, "Custom cake added to specialized cart! Please proceed to checkout.")
    return redirect('custom_cart')


@login_required
def verify_delivery(request, order_id):
    """Customer verifies delivery with OTP"""
    search_id = order_id if order_id.startswith('#') else f'#{order_id}'
    order = get_object_or_404(Order, order_id=search_id, customer=request.user)
    from .forms import DeliveryVerificationForm 

    if order.status == 'delivered':
        messages.info(request, "Order is already delivered.")
        return redirect('rate_order', order_id=order.order_id)
        
    if request.method == 'POST':
        form = DeliveryVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            
            if otp == order.delivery_otp:
                # Correct OTP
                order.status = 'delivered'
                order.delivered_at = timezone.now()
                order.delivery_otp = None # Clear OTP for security
                
                
                order.save()
                
                # Notification
                Notification.objects.create(
                    user=request.user,
                    notification_type='order_delivered',
                    title='Order Delivered',
                    message=f'Your order {order.order_id} has been delivered successfully.',
                    order=order
                )

                # Send Thank You Email
                from .utils import send_delivery_thank_you_email
                send_delivery_thank_you_email(
                    email=request.user.email,
                    order_id=order.order_id,
                    customer_name=request.user.get_full_name() or request.user.username
                )
                
                messages.success(request, "Delivery confirmed successfully! Please rate your experience.")
                return redirect('rate_order', order_id=order.order_id)
            else:
                messages.error(request, "Invalid OTP. Please try again.")
    else:
        form = DeliveryVerificationForm()
        
    context = {
        'order': order,
        'form': form
    }
    return render(request, 'verify_delivery.html', context)




@login_required
def rate_order(request, order_id):
    """Rate and review a delivered order"""
    search_id = order_id if order_id.startswith('#') else f'#{order_id}'
    order = get_object_or_404(Order, order_id=search_id, customer=request.user)
    
    if order.status != 'delivered':
        messages.error(request, "You can only rate delivered orders.")
        return redirect('my_orders')
        
    # Check if already rated
    if hasattr(order, 'review'):
        messages.info(request, "You have already rated this order.")
        return redirect('my_orders')

    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.order = order
            review.customer = request.user
            # Link to the first cake in order (simplification, ideally rate each item or the order as a whole)
            # For this system, we'll associate with the first cake if available, or just keeping it linked to order
            # The Review model requires a cake fk based on models.py
            if order.items.exists():
                review.cake = order.items.first().cake
            else:
                # Fallback if no items (shouldn't happen)
                 messages.error(request, "Order has no items to rate.")
                 return redirect('my_orders')
                 
            review.save()
            
            # Create Notification for Baker
            if review.cake.baker:
                message = f'New {review.rating} star rating for Order {order.order_id}.'
                if review.comment:
                    message += f'\nComment: {review.comment}'
                
                Notification.objects.create(
                    user=review.cake.baker,
                    notification_type='review_received',
                    title='New Review Received',
                    message=message,
                    order=order
                )
                
                # Send professional email to baker
                try:
                    shop_name = review.cake.baker.profile.baker_profile.shop_name
                except:
                    shop_name = review.cake.baker.username
                    
                send_baker_review_email(
                    email=review.cake.baker.email,
                    rating=review.rating,
                    comment=review.comment,
                    customer_name=request.user.get_full_name() or request.user.username,
                    baker_shop_name=shop_name
                )

            messages.success(request, "Thank you for your feedback!")
            return redirect('my_orders')
    else:
        form = ReviewForm()
        
    context = {
        'order': order,
        'form': form
    }
    return render(request, 'add_review.html', context)

@login_required
def baker_public_profile(request, baker_id):
    """Public profile view for a baker"""
    baker_profile = get_object_or_404(BakerProfile, id=baker_id, status='approved')
    cakes = Cake.objects.filter(baker=baker_profile.user_profile.user, is_available=True)

    # Count delivered orders for this baker
    delivered_orders_count = Order.objects.filter(
        items__cake__baker=baker_profile.user_profile.user,
        status='delivered'
    ).distinct().count()

    context = {
        'baker_profile': baker_profile,
        'cakes': cakes,
        'delivered_orders_count': delivered_orders_count,
    }
    return render(request, 'baker_public_profile.html', context)

@login_required
def baker_reviews(request, baker_id):
    """View all reviews for a baker"""
    baker_profile = get_object_or_404(BakerProfile, id=baker_id, status='approved')
    
    # Get all reviews for cakes made by this baker
    reviews = Review.objects.filter(
        cake__baker=baker_profile.user_profile.user,
        is_approved=True
    ).order_by('-created_at')
    
    context = {
        'baker_profile': baker_profile,
        'reviews': reviews,
    }
    return render(request, 'baker_reviews.html', context)

