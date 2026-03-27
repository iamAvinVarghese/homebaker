"""
Admin Module Views (Dark Theme Panel)
Includes: Admin Dashboard, System Analytics, User Management, Baker Approval
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from .models import (
    User, UserProfile, BakerProfile, Cake, Order, Expense, Review,
    Wallet, Notification, AuditLog, Coupon
)
from .ai_utils import BusinessInsights
from chatbot.service import ChatbotService
from .views_auth import log_audit
from .utils import send_approval_email, send_coupon_announcement


def is_admin(user):
    """Check if user is admin/staff"""
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard with system analytics"""
    # System KPIs
    total_users = UserProfile.objects.exclude(role='admin').count()
    total_customers = UserProfile.objects.filter(role='customer').count()
    total_bakers = UserProfile.objects.filter(role='baker').count()
    total_delivery_assistants = UserProfile.objects.filter(role='delivery_assistant').count()
    total_orders = Order.objects.exclude(status='cancelled').count()
    
    # Revenue overview
    total_revenue = Order.objects.filter(
        payment_status='paid',
        status='delivered'
    ).aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
    
    monthly_revenue_kpi = Order.objects.filter(
        created_at__gte=timezone.now().replace(day=1),
        payment_status='paid',
        status='delivered'
    ).aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
    
    # Platform commission
    total_commission = Decimal('0.00')
    for baker_profile in BakerProfile.objects.all():
        # Get total revenue and total coupon discounts for this baker's delivered orders
        order_stats = Order.objects.filter(
            items__cake__baker=baker_profile.user_profile.user,
            payment_status='paid',
            status='delivered'
        ).aggregate(
            total_rev=Sum('subtotal'),
            total_discount=Sum('coupon_discount')
        )
        
        baker_revenue = order_stats['total_rev'] or Decimal('0.00')
        baker_discounts = order_stats['total_discount'] or Decimal('0.00')
        
        # Commission is base % minus the discounts admin covered
        base_commission = baker_revenue * (baker_profile.commission_rate / 100)
        total_commission += (base_commission - baker_discounts)
    
    # Pending baker approvals
    pending_bakers = BakerProfile.objects.filter(status='pending').count()
    
    # Calculate admins (Total - Customers - Bakers) might be safer, or explicit count
    total_admins = UserProfile.objects.filter(role='admin').count()
    
    # Recent activity
    recent_orders = Order.objects.order_by('-created_at')[:10]
    recent_audit_logs = AuditLog.objects.order_by('-created_at')[:10]
    
    # Order statistics for dashboard
    unique_customer_count = Order.objects.values('customer').distinct().count()
    completed_orders_count = Order.objects.filter(status='delivered').count()
    pending_orders_count = Order.objects.exclude(status__in=['delivered', 'cancelled']).count()
    
    # Chart data
    chart_data = get_admin_chart_data()
    # json_script in template determines serialization, pass dict directly
    
    context = {
        'total_users': total_users,
        'total_customers': total_customers,
        'total_bakers': total_bakers,
        'total_delivery_assistants': total_delivery_assistants,
        'total_admins': total_admins,
        'total_orders': total_orders,
        'unique_customer_count': unique_customer_count,
        'completed_orders_count': completed_orders_count,
        'pending_orders_count': pending_orders_count,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue_kpi,
        'total_commission': total_commission,
        'pending_bakers': pending_bakers,
        'recent_orders': recent_orders,
        'recent_audit_logs': recent_audit_logs,
        'chart_data': chart_data,
    }
    return render(request, 'admin_dashboard.html', context)


def get_admin_chart_data():
    """Get data for admin charts - Dynamic with 'valid data' filter"""
    monthly_revenue = []
    user_growth = []
    
    today = timezone.now()
    
    # Start from January of the current year (month=1)
    # today.month gives current month (e.g., 2 for Feb)
    for i in range(today.month - 1, -1, -1):
        # Calculate target year and month
        target_year = today.year
        target_month = today.month - i
        
        # We don't need while loop here as we are strictly in the current year
        # but kept for robustness if logic changes
        while target_month <= 0:
            target_month += 12
            target_year -= 1
            
        month_label = date(target_year, target_month, 1).strftime('%b %Y')
        
        # Revenue (Paid only)
        revenue = Order.objects.filter(
            created_at__year=target_year,
            created_at__month=target_month,
            payment_status='paid',
            status='delivered'
        ).aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
        
        # User Growth (excluding admins)
        new_users = UserProfile.objects.exclude(role='admin').filter(
            user__date_joined__year=target_year,
            user__date_joined__month=target_month
        ).count()
        
        monthly_revenue.append({'month': month_label, 'revenue': float(revenue)})
        user_growth.append({'month': month_label, 'users': new_users})
    
    # Order status distribution
    status_distribution = []
    for status_code, status_name in Order.STATUS_CHOICES:
        count = Order.objects.filter(status=status_code).count()
        status_distribution.append({
            'status': status_name,
            'count': count
        })
    
    return {
        'monthly_revenue': monthly_revenue,
        'user_growth': user_growth,
        'status_distribution': status_distribution,
    }


@login_required
@user_passes_test(is_admin)
def admin_users(request):
    """Manage users"""
    users = User.objects.all().order_by('-date_joined')
    # Exclude admins from the list
    users = users.exclude(profile__role='admin')

    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(profile__role=role_filter)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query)
        )
    
    context = {
        'users': users,
        'role_filter': role_filter,
        'search_query': search_query,
    }
    return render(request, 'admin_users.html', context)


@login_required
@user_passes_test(is_admin)
def admin_bakers(request):
    """Manage bakers and approvals"""
    bakers = BakerProfile.objects.all().order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        bakers = bakers.filter(status=status_filter)
    
    # Statistics
    total_bakers = BakerProfile.objects.count()
    pending_bakers = BakerProfile.objects.filter(status='pending').count()
    approved_bakers = BakerProfile.objects.filter(status='approved').count()
    
    context = {
        'bakers': bakers,
        'status_filter': status_filter,
        'total_bakers': total_bakers,
        'pending_bakers': pending_bakers,
        'approved_bakers': approved_bakers,
    }
    return render(request, 'admin_bakers.html', context)


@login_required
@user_passes_test(is_admin)
def admin_approve_baker(request, baker_id):
    """Approve baker"""
    baker_profile = get_object_or_404(BakerProfile, id=baker_id)
    
    if request.method == 'POST':
        baker_profile.status = 'approved'
        baker_profile.save()
        
        # Create notification
        Notification.objects.create(
            user=baker_profile.user_profile.user,
            notification_type='baker_approved',
            title='Baker Account Approved',
            message='Your baker account has been approved. You can now start managing your cakes!'
        )
        
        # Send Email Notification
        send_approval_email(
            email=baker_profile.user_profile.user.email,
            is_approved=True,
            shop_name=baker_profile.shop_name
        )
        
        log_audit(
            request.user, 'approve', 'BakerProfile', baker_id,
            f'Approved baker: {baker_profile.shop_name}', request
        )
        
        messages.success(request, f'Baker {baker_profile.shop_name} approved and notified successfully!')
    
    return redirect('admin_bakers')


@login_required
@user_passes_test(is_admin)
def admin_reject_baker(request, baker_id):
    """Reject baker"""
    baker_profile = get_object_or_404(BakerProfile, id=baker_id)
    
    if request.method == 'POST':
        baker_profile.status = 'rejected'
        baker_profile.save()
        
        # Create notification
        Notification.objects.create(
            user=baker_profile.user_profile.user,
            notification_type='baker_rejected',
            title='Baker Account Rejected',
            message='Your baker account application has been rejected. Please contact support for more information.'
        )
        
        # Send Email Notification
        send_approval_email(
            email=baker_profile.user_profile.user.email,
            is_approved=False,
            shop_name=baker_profile.shop_name
        )
        
        log_audit(
            request.user, 'reject', 'BakerProfile', baker_id,
            f'Rejected baker: {baker_profile.shop_name}', request
        )
        
        messages.success(request, f'Baker {baker_profile.shop_name} rejected and notified.')
    
    return redirect('admin_bakers')


@login_required
@user_passes_test(is_admin)
def admin_suspend_user(request, user_id):
    """Suspend user account"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            profile = user.profile
            profile.is_suspended = True
            profile.save()
            
            log_audit(
                request.user, 'suspend', 'User', user_id,
                f'Suspended user: {user.username}', request
            )
            
            messages.success(request, f'User {user.get_full_name() or user.username} suspended.')
        except UserProfile.DoesNotExist:
            messages.error(request, 'User profile not found.')
    
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin)
def admin_block_user_temp(request, user_id):
    """Block user temporarily"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            profile = user.profile
            duration = int(request.POST.get('duration', 24)) # Default 24 hours
            profile.lock_account(hours=duration)
            
            log_audit(
                request.user, 'block_temp', 'User', user_id,
                f'Blocked user {user.username} for {duration} hours', request
            )
            
            messages.success(request, f'User {user.get_full_name() or user.username} blocked for {duration} hours.')
        except UserProfile.DoesNotExist:
            messages.error(request, 'User profile not found.')
    
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin)
def admin_unsuspend_user(request, user_id):
    """Unsuspend user account and clear blocks"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            profile = user.profile
            profile.is_suspended = False
            # Also clear temporary locks
            profile.unlock_account()
            profile.save()
            
            log_audit(
                request.user, 'unsuspend', 'User', user_id,
                f'Unsuspended/Unblocked user: {user.username}', request
            )
            
            messages.success(request, f'User {user.get_full_name() or user.username} activated and unblocked.')
        except UserProfile.DoesNotExist:
            messages.error(request, 'User profile not found.')
    
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin)
def admin_audit_logs(request):
    """View audit logs"""
    logs = AuditLog.objects.all().order_by('-created_at')[:100]
    
    # Filter by action
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    context = {
        'logs': logs,
        'action_filter': action_filter,
    }
    return render(request, 'admin_audit_logs.html', context)


@login_required
@user_passes_test(is_admin)
def admin_analytics(request):
    """Advanced analytics page"""
    # Revenue analytics
    revenue_data = BusinessInsights.get_revenue_analytics(days=30)
    
    # Top selling cakes (Group custom cakes together)
    all_cakes_with_sales = Cake.objects.annotate(
        sales_count=Count('order_items')
    ).filter(sales_count__gt=0)
    
    top_cakes_list = []
    custom_sales = 0
    
    for cake in all_cakes_with_sales:
        if cake.occasion == 'custom' or cake.name.startswith('Custom Cake Request #'):
            custom_sales += cake.sales_count
        else:
            try:
                shop_name = cake.baker.profile.baker_profile.shop_name
            except Exception:
                shop_name = cake.baker.get_full_name() if cake.baker else 'Unknown Baker'
                
            top_cakes_list.append({
                'name': cake.name,
                'baker': {'shop_name': shop_name},
                'sales_count': cake.sales_count
            })
            
    if custom_sales > 0:
        top_cakes_list.append({
            'name': 'Custom Cake Requests',
            'baker': {'shop_name': 'Various Bakers'},
            'sales_count': custom_sales
        })
        
    top_cakes_list.sort(key=lambda x: x['sales_count'], reverse=True)
    top_cakes = top_cakes_list[:10]
    
    # Create commission breakdown
    baker_commissions = []
    total_platform_commission = Decimal('0.00')
    
    for baker in BakerProfile.objects.all():
        # Get total revenue and total coupon discounts for this baker's delivered orders
        order_stats = Order.objects.filter(
            items__cake__baker=baker.user_profile.user,
            payment_status='paid',
            status='delivered'
        ).aggregate(
            total_rev=Sum('subtotal'),
            total_discount=Sum('coupon_discount')
        )
        
        baker_revenue = order_stats['total_rev'] or Decimal('0.00')
        baker_discounts = order_stats['total_discount'] or Decimal('0.00')
        
        base_commission = baker_revenue * (baker.commission_rate / 100)
        commission_amount = base_commission - baker_discounts
        total_platform_commission += commission_amount
        
        baker_commissions.append({
            'baker': baker,
            'revenue': baker_revenue,
            'commission_rate': baker.commission_rate,
            'commission_amount': commission_amount,
            'total_discounts_covered': baker_discounts
        })
    
    # Sort by commission amount (descending)
    baker_commissions.sort(key=lambda x: x['commission_amount'], reverse=True)
    
    # Top bakers (for top users card)
    top_bakers = BakerProfile.objects.order_by('-total_revenue')[:10]

    context = {
        'revenue_data': revenue_data,
        'top_cakes': top_cakes,
        'top_bakers': top_bakers,
        'baker_commissions': baker_commissions,
        'total_platform_commission': total_platform_commission,
    }
    return render(request, 'admin_analytics.html', context)


@login_required
@user_passes_test(is_admin)
def admin_revenue(request):
    """Detailed revenue analytics"""
    # Calculate revenue generated by each baker
    baker_revenues = []
    for baker in BakerProfile.objects.all():
        revenue = Order.objects.filter(
            items__cake__baker=baker.user_profile.user,
            payment_status='paid',
            status='delivered'
        ).aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
        
        baker_revenues.append({
            'baker': baker,
            'revenue': revenue
        })
    
    # Sort by revenue descending
    baker_revenues.sort(key=lambda x: x['revenue'], reverse=True)
    
    # Detailed payment logs
    payments = Order.objects.filter(payment_status='paid', status='delivered').order_by('-created_at')
    
    context = {
        'baker_revenues': baker_revenues,
        'payments': payments,
    }
    return render(request, 'admin_revenue.html', context)


@login_required
@user_passes_test(is_admin)
def admin_orders_list(request):
    """Detailed orders management and stats - Efficient Rewrite"""
    # Optimized query
    orders = Order.objects.select_related('customer').prefetch_related('items__cake__baker').all().order_by('-created_at')
    
    # Filters
    active_status = request.GET.get('status', '')
    if active_status:
        orders = orders.filter(status=active_status)
        
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(
            Q(order_id__icontains=search_query) |
            Q(customer__username__icontains=search_query) |
            Q(customer__first_name__icontains=search_query)
        )
        
    # Aggragated Stats
    total_count = Order.objects.exclude(status='cancelled').count()
    status_counts = Order.objects.values('status').annotate(count=Count('id'))
    today_orders = Order.objects.filter(created_at__date=timezone.now().date()).count()
    total_revenue = Order.objects.filter(payment_status='paid', status='delivered').aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
    
    # Map status counts for easy access
    stats_dict = {item['status']: item['count'] for item in status_counts}
    
    context = {
        'orders': orders,
        'active_status': active_status,
        'search_query': search_query,
        'total_count': total_count,
        'today_orders': today_orders,
        'total_revenue': total_revenue,
        'stats_dict': stats_dict,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'admin_orders_list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_commission(request):
    """Commission breakdown analysis"""
    baker_commissions = []
    total_platform_commission = Decimal('0.00')
    
    for baker in BakerProfile.objects.all():
        # Get total revenue and total coupon discounts for this baker's delivered orders
        order_stats = Order.objects.filter(
            items__cake__baker=baker.user_profile.user,
            payment_status='paid',
            status='delivered'
        ).aggregate(
            total_rev=Sum('subtotal'),
            total_discount=Sum('coupon_discount')
        )
        
        baker_revenue = order_stats['total_rev'] or Decimal('0.00')
        baker_discounts = order_stats['total_discount'] or Decimal('0.00')
        
        base_commission = baker_revenue * (baker.commission_rate / 100)
        commission_amount = base_commission - baker_discounts
        total_platform_commission += commission_amount
        
        baker_commissions.append({
            'baker': baker,
            'revenue': baker_revenue,
            'commission_rate': baker.commission_rate,
            'commission_amount': commission_amount,
            'total_discounts_covered': baker_discounts
        })
    
    baker_commissions.sort(key=lambda x: x['commission_amount'], reverse=True)
    
    context = {
        'baker_commissions': baker_commissions,
        'total_platform_commission': total_platform_commission,
    }
    return render(request, 'admin_commission.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_detail(request, user_id):
    """View detailed user/baker profile"""
    user_obj = get_object_or_404(User, id=user_id)
    
    # Get associated profiles
    try:
        profile = user_obj.profile
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('admin_users')
        
    baker_profile = None
    if profile.role == 'baker':
        try:
            baker_profile = profile.baker_profile
        except BakerProfile.DoesNotExist:
            pass
            
    # Get recent orders for this user (if customer)
    user_orders = Order.objects.filter(customer=user_obj).order_by('-created_at')[:10]
    
    # Get baker specific stuff
    baker_cakes = []
    if baker_profile:
        baker_cakes = Cake.objects.filter(baker=user_obj).order_by('-created_at')[:10]
        
    context = {
        'user_obj': user_obj,
        'profile': profile,
        'baker_profile': baker_profile,
        'user_orders': user_orders,
        'baker_cakes': baker_cakes,
    }
    return render(request, 'admin_user_detail.html', context)


@login_required
@user_passes_test(is_admin)
def admin_helpdesk(request):
    """Admin Help Desk: View all user support tickets"""
    from .models import SupportTicket
    
    tickets = SupportTicket.objects.select_related('user').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        tickets = tickets.filter(
            Q(subject__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query)
        )
    
    total_tickets = SupportTicket.objects.count()
    open_tickets = SupportTicket.objects.filter(status='open').count()
    resolved_tickets = SupportTicket.objects.filter(status='resolved').count()
    
    if request.method == 'POST':
        ticket_id = request.POST.get('ticket_id')
        new_status = request.POST.get('new_status')
        resolution_message = request.POST.get('resolution_message', '')
        
        if ticket_id and new_status:
            ticket = get_object_or_404(SupportTicket, id=ticket_id)
            ticket.resolution_message = resolution_message
            
            # Check if status is transitioning to resolved
            if new_status == 'resolved' and ticket.status != 'resolved':
                from .utils import send_ticket_resolved_email
                
                # Notification Message
                notif_msg = f"Your support ticket #{ticket.id} regarding '{ticket.subject}' has been marked as resolved by our team."
                if resolution_message:
                    notif_msg += f" Message from admin: {resolution_message}"
                
                # Create In-App Notification
                Notification.objects.create(
                    user=ticket.user,
                    notification_type='ticket_resolved',
                    title='Support Ticket Resolved',
                    message=notif_msg
                )
                
                # Send Professional Email
                send_ticket_resolved_email(
                    email=ticket.user.email,
                    customer_name=ticket.user.get_full_name() or ticket.user.username,
                    ticket_subject=ticket.subject,
                    ticket_id=ticket.id,
                    resolution_message=resolution_message
                )
            
            ticket.status = new_status
            ticket.save()
            messages.success(request, f'Ticket #{ticket_id} status updated to "{new_status}".')
            return redirect('admin_helpdesk')
    
    context = {
        'tickets': tickets,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'resolved_tickets': resolved_tickets,
    }
    return render(request, 'admin_helpdesk.html', context)
@login_required
@user_passes_test(is_admin)
def admin_coupons(request):
    """Admin coupon management view"""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        discount_type = request.POST.get('discount_type')
        discount_value = Decimal(request.POST.get('discount_value', '0'))
        min_order = Decimal(request.POST.get('min_order_amount', '0'))
        max_discount = request.POST.get('max_discount_amount')
        valid_until = request.POST.get('valid_until')
        usage_limit = request.POST.get('usage_limit')

        if not code:
            messages.error(request, 'Coupon code is required.')
        elif discount_type != 'percent' or not (Decimal('1') <= discount_value <= Decimal('10')):
            messages.error(request, 'Invalid discount. Only percentages between 1 and 10 are allowed.')
        else:
            try:
                coupon = Coupon(
                    code=code,
                    discount_type=discount_type,
                    discount_value=discount_value,
                    min_order_amount=min_order
                )
                if max_discount:
                    coupon.max_discount_amount = Decimal(max_discount)
                if valid_until:
                    coupon.valid_until = valid_until
                if usage_limit:
                    coupon.usage_limit = int(usage_limit)
                
                coupon.save()
                coupon.refresh_from_db() # Ensure date strings are converted to datetime objects
                messages.success(request, f'Coupon {code} created successfully!')
                log_audit(request.user, 'COUPON_CREATE', 'Coupon', coupon.id, f'Created coupon {code}', request)
                
                # Notify all customers
                customers = UserProfile.objects.filter(role='customer')
                for customer_profile in customers:
                    # In-app notification
                    Notification.objects.create(
                        user=customer_profile.user,
                        notification_type='coupon_launched',
                        title='New Discount Available! 🎁',
                        message=f'Use code {code} to get {coupon.discount_value}% off on your next order!'
                    )
                    # Email notification
                    send_coupon_announcement(
                        email=customer_profile.user.email,
                        customer_name=customer_profile.user.first_name or customer_profile.user.username,
                        coupon=coupon
                    )
            except Exception as e:
                messages.error(request, f'Error creating coupon: {str(e)}')
        
        return redirect('admin_coupons')

    coupons = Coupon.objects.all().order_by('-created_at')
    context = {
        'coupons': coupons,
        'now': timezone.now()
    }
    return render(request, 'admin_coupons.html', context)


@login_required
@user_passes_test(is_admin)
def admin_delete_coupon(request, coupon_id):
    """Delete a coupon gracefully"""
    try:
        coupon = Coupon.objects.get(id=coupon_id)
        code = coupon.code
        coupon.delete()
        messages.success(request, f'Coupon {code} deleted successfully.')
        log_audit(request.user, 'COUPON_DELETE', 'Coupon', coupon_id, f'Deleted coupon {code}', request)
    except Coupon.DoesNotExist:
        messages.error(request, 'This coupon does not exist or has already been deleted.')
    
    return redirect('admin_coupons')
