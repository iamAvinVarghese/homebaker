"""
Baker Module Views
Includes: Dashboard with KPIs, Charts, Cake Management, Expense Tracking, Order Handling
Updated: Baker Orders added
"""

import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg
from django.http import JsonResponse
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json
from datetime import timedelta
from decimal import Decimal
from .models import (
    Cake, Order, OrderItem, Expense, BakerProfile, Notification, Wallet,
    CustomCakeRequest, UserProfile
)
from .forms import CakeForm, ExpenseForm
from .utils import send_custom_request_status_email, send_order_acceptance_email, send_delivery_otp_email
from .ai_utils import BusinessInsights, SmartPricing, RecommendationEngine


@login_required
def baker_dashboard(request):
    """Baker dashboard with KPIs and charts"""
    # Check if user is a baker
    try:
        profile = request.user.profile
        if profile.role != 'baker':
            messages.warning(request, 'You do not have access to the baker dashboard.')
            return redirect('home')
        
        baker_profile = profile.baker_profile
        if baker_profile.status != 'approved':
            messages.warning(request, 'Your baker account is pending approval.')
    except (UserProfile.DoesNotExist, BakerProfile.DoesNotExist):
        messages.warning(request, 'Please complete your baker profile.')
        return redirect('home')
    
    # Get baker's orders
    baker_orders = Order.objects.filter(
        items__cake__baker=request.user
    ).distinct()
    
    # Calculate KPIs
    total_orders = baker_orders.exclude(status='cancelled').count()
    total_delivered = baker_orders.filter(status='delivered').count()
    
    # Monthly revenue
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
    monthly_revenue = baker_orders.filter(
        created_at__gte=current_month_start,
        payment_status='paid',
        status='delivered'
    ).aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')

    # Total Lifetime Revenue
    total_lifetime_revenue = baker_orders.filter(
        payment_status='paid',
        status='delivered'
    ).aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
    
    # Total profit (revenue - expenses - commission)
    profit_data = BusinessInsights.get_profit_analytics(request.user, days=30)
    total_profit = profit_data['profit']
    
    # Total Expenses (Lifetime) - Calculated as 40% of (Revenue - Commission)
    # Commission is 10%
    total_commission = total_lifetime_revenue * Decimal('0.10')
    total_expenses = (total_lifetime_revenue - total_commission) * Decimal('0.40')
    
    # Recalculate Profit based on this logic to be consistent
    # Profit = Revenue - Commission - Expenses
    total_profit = total_lifetime_revenue - total_commission - total_expenses
    
    # Custom Requests
    pending_custom_requests = CustomCakeRequest.objects.filter(baker=baker_profile, status='PENDING').count()
    
    # Average rating
    avg_rating = baker_profile.average_rating
    
    # Get chart data
    chart_data = get_baker_chart_data(request.user)
    # Get chart data
    chart_data = get_baker_chart_data(request.user)
    
    # Recent orders
    recent_orders = baker_orders.order_by('-created_at')[:10]
    
    
    context = {
        'total_orders': total_orders,
        'total_delivered': total_delivered,
        'monthly_revenue': monthly_revenue,
        'total_revenue': total_lifetime_revenue,
        'total_expenses': total_expenses,
        'total_profit': total_profit,
        'average_rating': avg_rating,
        'pending_custom_requests': pending_custom_requests,
        'chart_data': chart_data,
    }
    return render(request, 'baker_dashboard.html', context)


def get_baker_chart_data(baker):
    """Get data for Chart.js charts"""
    monthly_revenue_data = []
    monthly_expenses_data = []
    monthly_profit_data = []
    
    # Combined loop for Revenue, Expenses, and Profit - Last 6 months
    for i in range(5, -1, -1):
        month_start = (timezone.now() - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Calculate Revenue for this specific month
        revenue = Order.objects.filter(
            items__cake__baker=baker,
            created_at__gte=month_start,
            created_at__lte=month_end,
            payment_status='paid',
            status='delivered'
        ).aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
        
        rev_float = float(revenue)
        
        # Monthly Revenue Data
        monthly_revenue_data.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': rev_float
        })
        
        # Calculate Commission (10%) and Expenses (40% of Revenue - Commission)
        commission = revenue * Decimal('0.10')
        expenses = (revenue - commission) * Decimal('0.40')
        profit = revenue - commission - expenses
        
        # Monthly Expenses Data
        monthly_expenses_data.append({
            'month': month_start.strftime('%b %Y'),
            'expenses': float(expenses)
        })
        
        # Monthly Profit Data
        monthly_profit_data.append({
            'month': month_start.strftime('%b %Y'),
            'profit': float(profit)
        })
    
    # Popular Cakes (Donut Chart)
    # Group all custom cakes (occasion='custom') into one entry
    all_cakes = Cake.objects.filter(baker=baker).annotate(
        total_orders=Count('order_items')
    ).filter(total_orders__gt=0)
    
    custom_orders_sum = 0
    regular_cakes_data = []
    
    for cake in all_cakes:
        if cake.occasion == 'custom' or cake.name.startswith('Custom Cake Request #'):
            custom_orders_sum += cake.total_orders
        else:
            regular_cakes_data.append({
                'name': cake.name,
                'orders': cake.total_orders
            })
    
    # Combine regular cakes with the "Custom Cakes" unit
    popular_cakes_data = regular_cakes_data
    if custom_orders_sum > 0:
        popular_cakes_data.append({
            'name': 'Custom Cakes',
            'orders': custom_orders_sum
        })
    
    # Sort by orders desc and take top 5
    popular_cakes_data = sorted(popular_cakes_data, key=lambda x: x['orders'], reverse=True)[:5]
    
    return {
        'monthly_revenue': monthly_revenue_data,
        'monthly_expenses': monthly_expenses_data,
        'monthly_profit': monthly_profit_data,
        'popular_cakes': popular_cakes_data,
    }


@login_required
def baker_cakes(request):
    """Manage cakes"""
    # Check baker access
    try:
        if request.user.profile.role != 'baker':
            return redirect('home')
    except:
        return redirect('home')
    
    cakes = Cake.objects.filter(baker=request.user).exclude(name__startswith='Custom Cake Request #').order_by('-created_at')
    
    context = {
        'cakes': cakes,
    }
    return render(request, 'baker_cakes.html', context)


@login_required
def baker_add_cake(request):
    """Add new cake"""
    try:
        profile = request.user.profile
        if profile.role != 'baker':
            return redirect('home')
        
        baker_profile = profile.baker_profile
        if baker_profile.status != 'approved':
            messages.error(request, 'Your baker account must be approved before you can add cakes.')
            return redirect('baker_cakes')
    except (UserProfile.DoesNotExist, BakerProfile.DoesNotExist):
        return redirect('home')
    
    if request.method == 'POST':
        form = CakeForm(request.POST, request.FILES)
        if form.is_valid():
            cake = form.save(commit=False)
            cake.baker = request.user
            cake.save()
            messages.success(request, 'Cake added successfully!')
            return redirect('baker_cakes')
    else:
        form = CakeForm()
    
    context = {
        'form': form,
    }
    return render(request, 'baker_add_cake.html', context)


@login_required
def baker_edit_cake(request, cake_id):
    """Edit cake"""
    try:
        if request.user.profile.baker_profile.status != 'approved':
            messages.error(request, 'Your baker account must be approved before you can edit cakes.')
            return redirect('baker_cakes')
    except:
        return redirect('home')

    cake = get_object_or_404(Cake, id=cake_id, baker=request.user)
    
    if request.method == 'POST':
        form = CakeForm(request.POST, request.FILES, instance=cake)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cake updated successfully!')
            return redirect('baker_cakes')
    else:
        form = CakeForm(instance=cake)
    
    context = {
        'form': form,
        'cake': cake,
    }
    return render(request, 'baker_edit_cake.html', context)


@login_required
def baker_expenses(request):
    """Manage expenses"""
    # Check baker access
    try:
        if request.user.profile.role != 'baker':
            return redirect('home')
    except:
        return redirect('home')
    
    expenses = Expense.objects.filter(baker=request.user).order_by('-expense_date', '-created_at')
    
    # Calculate totals
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    monthly_expenses = Expense.objects.filter(
        baker=request.user,
        expense_date__gte=timezone.now().replace(day=1).date()
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.baker = request.user
            expense.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('baker_expenses')
    else:
        form = ExpenseForm()
    
    context = {
        'expenses': expenses,
        'form': form,
        'total_expenses': total_expenses,
        'monthly_expenses': monthly_expenses,
    }
    return render(request, 'baker_expenses.html', context)





@login_required
def baker_delete_cake(request, cake_id):
    """Delete a cake"""
    # Check baker access
    try:
        if request.user.profile.role != 'baker':
            return redirect('home')
    except:
        return redirect('home')
        
    cake = get_object_or_404(Cake, id=cake_id, baker=request.user)
    
    if request.method == 'POST':
        cake.delete()
        messages.success(request, 'Cake deleted successfully!')
        return redirect('baker_cakes')
    
    # If not POST, redirect back to list
    return redirect('baker_cakes')


@login_required
def manage_baker_orders(request):
    """Manage orders - View pending and active orders"""
    # Check baker access
    try:
        if request.user.profile.role != 'baker':
            return redirect('home')
    except:
        return redirect('home')
    
    # Get all orders containing items from this baker
    orders = Order.objects.filter(
        items__cake__baker=request.user
    ).distinct().order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'baker_orders.html', context)


@login_required
def baker_accept_order(request, order_id):
    """Accept order and credit wallet"""
    # Check baker access
    try:
        profile = request.user.profile
        if profile.role != 'baker':
            return redirect('home')
    except:
        return redirect('home')

    order = get_object_or_404(Order, id=order_id)
    
    # Verify baker has items in this order
    baker_items = order.items.filter(cake__baker=request.user)
    if not baker_items.exists():
        messages.error(request, 'You do not have permission to accept this order.')
        return redirect('baker_orders')
    
    # Only allow acceptance if order is pending
    if order.status != 'pending':
        messages.warning(request, 'This order has already been processed.')
        return redirect('baker_orders')
    
    # 1. Update Order Status (Straight to confirmed, no OTP)
    order.status = 'confirmed'
    order.save()
    
    # 2. Notify Customer (Database)
    Notification.objects.create(
        user=order.customer,
        notification_type='order_confirmed',
        title=f'Order {order.order_id} Accepted',
        message=f'Your order has been accepted by the baker and will reach its destination in time.',
        order=order
    )
    
    # 3. Send Confirmation Email via Utility
    try:
        shop_name = request.user.profile.baker_profile.shop_name
    except:
        shop_name = "Our Baker"

    customer_name = order.customer.get_full_name() or order.customer.username
    
    send_order_acceptance_email(
        email=order.customer.email,
        order_id=order.order_id,
        customer_name=customer_name,
        baker_shop_name=shop_name
    )

    messages.success(request, f'Order accepted! Confirmation email sent to {order.customer.email}.')
    return redirect('baker_orders')
@login_required
def baker_custom_requests(request):
    """View to list and manage custom cake requests for a baker"""
    try:
        user_profile = request.user.profile
        baker_profile = user_profile.baker_profile
    except (UserProfile.DoesNotExist, BakerProfile.DoesNotExist):
        messages.error(request, 'Please complete your baker profile.')
        return redirect('home')
        
    custom_requests = CustomCakeRequest.objects.filter(baker=baker_profile)
    
    context = {
        'custom_requests': custom_requests,
    }
    return render(request, 'baker/custom_requests.html', context)


@login_required
def respond_to_custom_request(request, request_id):
    """View for baker to accept or reject a custom request"""
    custom_request = get_object_or_404(CustomCakeRequest, id=request_id)
    
    # Security check: ensure baker owns this request
    if custom_request.baker.user_profile.user != request.user:
        messages.error(request, 'Unauthorized access.')
        return redirect('baker_dashboard')
        
    if custom_request.status != 'PENDING':
        messages.error(request, f'This request is already {custom_request.get_status_display()}.')
        return redirect('baker_custom_requests')
        
    if request.method == 'POST':
        action = request.POST.get('action') # 'accept' or 'reject'
        price_quote = request.POST.get('price_quote')
        baker_message = request.POST.get('baker_message')
        
        if action == 'accept':
            try:
                if price_quote:
                    custom_request.price_quote = Decimal(price_quote)
                    custom_request.status = 'ACCEPTED'
                    messages.success(request, "Request accepted successfully!")
                else:
                    messages.error(request, "Price quote is required to accept.")
                    return redirect('baker_custom_requests')
            except Exception:
                 messages.error(request, "Invalid price quote.")
                 return redirect('baker_custom_requests')
                 
        elif action == 'reject':
            custom_request.status = 'REJECTED'
            messages.success(request, "Request rejected.")
            
        custom_request.baker_message = baker_message
        custom_request.save()
        
        # Create Notification for Customer
        Notification.objects.create(
            user=custom_request.customer,
            notification_type='custom_request_accepted' if custom_request.status == 'ACCEPTED' else 'custom_request_rejected',
            title=f"Custom Request {'Accepted' if custom_request.status == 'ACCEPTED' else 'Rejected'}",
            message=f"Your custom cake request '{custom_request.description[:30]}...' has been {'accepted (₹' + str(custom_request.price_quote) + ')' if custom_request.status == 'ACCEPTED' else 'rejected'} by {custom_request.baker.shop_name}.",
        )
        
        # Send Email Notification to Customer
        send_custom_request_status_email(
            email=custom_request.customer.email,
            status=custom_request.status,
            cake_name=custom_request.description[:50] + "...", # Use description snippet as name
            baker_name=custom_request.baker.shop_name,
            baker_message=custom_request.baker_message,
            price_quote=custom_request.price_quote
        )
        
    return redirect('baker_custom_requests')


@login_required
def trigger_delivery(request, order_id):
    """Generate OTP and mark order as out for delivery"""
    # Check baker access
    try:
        if request.user.profile.role != 'baker':
            return redirect('home')
    except:
        return redirect('home')

    order = get_object_or_404(Order, id=order_id)
    
    # Check if this baker is part of the order
    if not order.items.filter(cake__baker=request.user).exists():
        messages.error(request, "Unauthorized access to this order.")
        return redirect('baker_orders')

    if order.status not in ['confirmed', 'baking', 'packing', 'ready']:
        # If already out for delivery or delivered, just inform user
        if order.status == 'out_for_delivery':
             messages.info(request, f"Order is already out for delivery. OTP: {order.delivery_otp}")
             return redirect('baker_orders')
        elif order.status == 'delivered':
             messages.info(request, "Order is already delivered.")
             return redirect('baker_orders')
        
        messages.error(request, "Order is not ready for delivery yet.")
        return redirect('baker_orders')

    import random
    from django.core.mail import send_mail
    from django.conf import settings

    # Generate 4-digit OTP
    otp = str(random.randint(1000, 9999))
    
    # Update Order
    order.delivery_otp = otp
    order.status = 'out_for_delivery'
    order.save()
    
    # Create Notification for Customer
    Notification.objects.create(
        user=order.customer,
        notification_type='order_ready',
        title=f'Order {order.order_id} Ready for Pickup - OTP: {otp}',
        message=f'Your order is ready! Please share OTP {otp} with the delivery partner upon arrival/pickup.',
        order=order
    )
    
    # Send Email to Customer via Professional Template
    customer_fullname = order.customer.get_full_name() or order.customer.username
    
    email_sent = send_delivery_otp_email(
        email=order.customer.email,
        otp=otp,
        order_id=order.order_id,
        customer_name=customer_fullname
    )
    
    if email_sent:
        messages.success(request, f"Order marked 'Ready for Pickup'. OTP sent to customer.")
    else:
        messages.warning(request, f"Order status updated. Manual OTP: {otp} (Email failed)")

    return redirect('baker_orders')


@login_required
def baker_ai_analytics(request):
    """Dedicated AI Analytics page for Bakers"""
    try:
        profile = request.user.profile
        if profile.role != 'baker':
            messages.warning(request, 'Access denied.')
            return redirect('home')
        baker_profile = profile.baker_profile
    except (UserProfile.DoesNotExist, BakerProfile.DoesNotExist):
        return redirect('home')

    # Get insights
    insights = BusinessInsights.generate_insights(baker=request.user)
    
    # Get growth prediction
    growth_data = BusinessInsights.get_growth_prediction(baker=request.user, days=30)
    
    context = {
        'insights': insights,
        'growth_data': growth_data,
        'average_rating': baker_profile.average_rating,
    }
    return render(request, 'baker_ai_analytics.html', context)


@login_required
def baker_cancel_order(request, order_id):
    """Baker cancels an order and refunds customer if necessary"""
    # Check baker access
    try:
        if request.user.profile.role != 'baker':
            return redirect('home')
    except:
        return redirect('home')

    order = get_object_or_404(Order, id=order_id)

    # Check if this baker is part of the order
    if not order.items.filter(cake__baker=request.user).exists():
        messages.error(request, "Unauthorized access to this order.")
        return redirect('baker_orders')

    if order.status not in ['pending', 'awaiting_confirmation', 'confirmed', 'baking', 'packing', 'ready', 'delivered']:
        messages.error(request, f"Order cannot be cancelled in its current state: {order.get_status_display()}")
        return redirect('baker_orders')

    if request.method == 'POST':
        # Reversal Logic if the order was already paid and potentially delivered (payouts processed)
        is_delivered = order.status == 'delivered'
        
        with transaction.atomic():
            if order.payment_status == 'paid':
                # 1. Full Refund to Customer (Always total_amount)
                Wallet.add_transaction(
                    user=order.customer,
                    transaction_type='credit',
                    amount=order.total_amount,
                    source='refund',
                    description=f'Baker Refund for Order {order.order_id}',
                    order=order
                )
                
                # 2. Reversals for Service Providers (only if payouts were sent - i.e. if it was delivered)
                if is_delivered:
                    # Reverse Baker Payout
                    baker_items = order.items.filter(cake__baker__isnull=False)
                    if baker_items.exists():
                        baker = baker_items.first().cake.baker
                        baker_revenue = sum(item.subtotal for item in baker_items)
                        try:
                            rate = baker.profile.baker_profile.commission_rate
                        except:
                            rate = Decimal('10.00')
                        
                        baker_revenue = Decimal(str(baker_revenue))
                        comm_amount = baker_revenue * (rate / Decimal('100.00'))
                        baker_payout = baker_revenue - comm_amount
                        
                        # Debit Baker
                        Wallet.add_transaction(
                            user=baker,
                            transaction_type='debit',
                            amount=baker_payout,
                            source='refund',
                            description=f'Reversal: Cancelled Delivered Order {order.order_id}',
                            order=order
                        )
                        
                        # Debit Admin Commission
                        if comm_amount > 0:
                            admin_profile = UserProfile.objects.filter(role='admin').first()
                            if admin_profile:
                                Wallet.add_transaction(
                                    user=admin_profile.user,
                                    transaction_type='debit',
                                    amount=comm_amount,
                                    source='reversal',
                                    description=f'Commission Reversal: Cancelled Order {order.order_id}',
                                    order=order
                                )

                    # Reverse Delivery Assistant Payout
                    # We need to find who delivered it. Usually the request.user is the baker here.
                    # We can find the transaction for this order with source='order' and 'Delivery Fee' description
                    delivery_txn = Wallet.objects.filter(
                        order=order, 
                        source='order', 
                        description__icontains='Delivery Fee',
                        transaction_type='credit'
                    ).first()
                    
                    if delivery_txn:
                        Wallet.add_transaction(
                            user=delivery_txn.user,
                            transaction_type='debit',
                            amount=delivery_txn.amount,
                            source='reversal',
                            description=f'Delivery Fee Reversal: Cancelled Order {order.order_id}',
                            order=order
                        )

                order.payment_status = 'refunded'
                messages.success(request, f'Order cancelled and ₹{order.total_amount} refunded to customer wallet.')
            else:
                messages.success(request, 'Order cancelled successfully.')

            order.status = 'cancelled'
            order.save()

            # Notify Customer
            Notification.objects.create(
                user=order.customer,
                notification_type='order_cancelled',
                title=f'Order {order.order_id} Cancelled by Baker',
                message=f'Your order {order.order_id} has been cancelled by the baker. A full refund of ₹{order.total_amount} has been added to your wallet.',
                order=order
            )

        return redirect('baker_orders')

    # If GET, show confirmation (can be a simple modal or extra page, here redirect back)
    return redirect('baker_orders')
