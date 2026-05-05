from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from email.mime.image import MIMEImage
import logging
import os

logger = logging.getLogger(__name__)

def send_premium_email(subject, template_name, context, recipient_list):
    """
    Helper function to send luxury emails with inline header image.
    """
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list if isinstance(recipient_list, list) else [recipient_list]
    )
    email.attach_alternative(html_content, "text/html")
    
    # Email header image attachment removed as per user request
    
    try:
        email.send()
        return True
    except Exception as e:
        logger.error(f"Error sending premium email: {e}")
        return False

def send_otp_email(email, otp, purpose="registration"):
    subject = f"Your {purpose.capitalize()} OTP - HomeBaker"
    context = {
        'subject': subject,
        'purpose': purpose.capitalize(),
        'otp': otp,
    }
    return send_premium_email(subject, 'emails/otp_email.html', context, email)

def send_delivery_otp_email(email, otp, order_id, customer_name):
    subject = f"Order {order_id} is Ready for Pickup - HomeBaker"
    context = {
        'subject': subject,
        'purpose': "Delivery Confirmation",
        'otp': otp,
        'customer_name': customer_name,
        'order_id': order_id,
        'is_delivery': True,
    }
    return send_premium_email(subject, 'emails/otp_email.html', context, email)

def send_approval_email(email, is_approved, shop_name):
    status = "Approved" if is_approved else "Rejected"
    subject = f"Baker Account {status} - HomeBaker"
    context = {
        'subject': subject,
        'status': status,
        'title': "Welcome to Home Baker!" if is_approved else "Application Status Update",
        'message': f"Congratulations! Your baker account for '{shop_name}' has been approved." if is_approved else f"Unfortunately, your baker account application for '{shop_name}' has been rejected at this time.",
        'details': {
            'Shop Name': shop_name,
            'Status': status
        },
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/login/" if is_approved else None,
        'action_text': "Log in to Dashboard" if is_approved else None,
    }
    return send_premium_email(subject, 'emails/status_email.html', context, email)

def send_custom_request_status_email(email, status, cake_name, baker_name, baker_message, price_quote=None):
    status_label = status.capitalize()
    subject = f"Custom Cake Request {status_label} - HomeBaker"
    context = {
        'subject': subject,
        'status': status.capitalize(),
        'title': "Request Accepted!" if status == 'ACCEPTED' else "Request Status Update",
        'message': f"Hello, your custom cake request for '{cake_name}' has been {status.lower()} by {baker_name}.",
        'details': {
            'Cake': cake_name,
            'Baker': baker_name,
            'Status': status_label,
            'Price Quote': f"₹{price_quote}" if price_quote else "TBD",
            'Baker Message': baker_message or 'No specific reason provided.'
        },
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/my-custom-requests/" if status == 'ACCEPTED' else None,
        'action_text': "View Request" if status == 'ACCEPTED' else None,
    }
    return send_premium_email(subject, 'emails/status_email.html', context, email)

def send_delivery_thank_you_email(email, order_id, customer_name):
    subject = f"Thank You for Your Order {order_id}! - HomeBaker"
    context = {
        'subject': subject,
        'title': "Delicious News!",
        'customer_name': customer_name,
        'order_id': order_id,
        'intro_text': f"Your order {order_id} has been delivered successfully!",
        'footer_text': "We hope you enjoy every bite of your cake. Your support means a lot to us and our home bakers. If you have a moment, please rate your experience on our platform!",
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/my-orders/",
        'action_text': "Rate Your Order"
    }
    return send_premium_email(subject, 'emails/order_details_email.html', context, email)

def send_order_placed_email(email, order, customer_name):
    subject = f"Congratulations! Your Order {order.order_id} is Placed - HomeBaker"
    context = {
        'subject': subject,
        'title': "Congratulations!",
        'customer_name': customer_name,
        'order_id': order.order_id,
        'amount': order.total_amount,
        'delivery_date': order.delivery_date,
        'address': order.delivery_address,
        'intro_text': f"Your order {order.order_id} has been placed successfully!",
        'footer_text': "Our baker(s) have been notified and will start working on your delicious treats soon. You can track your order status in your profile.",
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/my-orders/",
        'action_text': "Track Status"
    }
    return send_premium_email(subject, 'emails/order_details_email.html', context, email)

def send_baker_delivery_notification_email(email, order_id, baker_shop_name, payout_amount):
    subject = f"Delivery Completed for Order {order_id} - HomeBaker"
    context = {
        'subject': subject,
        'status': 'Accepted',
        'title': "Order Delivered!",
        'message': f"Hi {baker_shop_name}, we are happy to inform you that order {order_id} has been successfully delivered by our assistant.",
        'details': {
            'Order ID': order_id,
            'Payout Status': f"₹{payout_amount} credited to your wallet"
        },
        'footer_text': "The payment has been automatically processed and updated in your wallet balance. Keep up the great work!",
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/profile/",
        'action_text': "View Wallet"
    }
    return send_premium_email(subject, 'emails/status_email.html', context, email)

def send_order_acceptance_email(email, order_id, customer_name, baker_shop_name):
    subject = f"Baker Accepted Your Order {order_id} - HomeBaker"
    context = {
        'subject': subject,
        'status': 'Accepted',
        'title': "Good News! Your Order is Accepted",
        'message': f"Hi, we are happy to inform you that your order {order_id} has been accepted by {baker_shop_name}.",
        'details': {
            'Order ID': order_id,
            'Baker': baker_shop_name,
            'Status': 'Accepted - Preparing'
        },
        'footer_text': "The baker has started preparing your order, and it will reach the destination in time. You can track the progress of your order in your profile.",
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/my-orders/",
        'action_text': "View Orders"
    }
    return send_premium_email(subject, 'emails/status_email.html', context, email)

def send_baker_new_order_email(email, order, baker_shop_name):
    subject = f"New Order Received {order.order_id} - HomeBaker"
    baker_items = order.items.filter(cake__baker__email=email)
    baker_subtotal = sum(item.subtotal for item in baker_items)
    items_details = [f"{item.cake.name} - {item.quantity}kg" for item in baker_items]
    items_text = ", ".join(items_details) if items_details else "Check dashboard"

    context = {
        'subject': subject,
        'status': 'Accepted',
        'title': "New Order Received!",
        'message': f"Hi {baker_shop_name}, you have received a new order {order.order_id}.",
        'details': {
            'Order ID': order.order_id,
            'Items': items_text,
            'Baker Subtotal': f"₹{baker_subtotal}",
            'Total Amount': f"₹{order.total_amount}",
            'Delivery Date': order.delivery_date.strftime('%d %b %Y') if hasattr(order.delivery_date, 'strftime') else (order.delivery_date or 'N/A')
        },
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/baker/orders/",
        'action_text': "View Order Details"
    }
    return send_premium_email(subject, 'emails/status_email.html', context, email)

def send_baker_order_cancelled_email(email, order_id, baker_shop_name, reason=None):
    subject = f"Order Cancelled: {order_id} - HomeBaker"
    context = {
        'subject': subject,
        'status': 'Rejected',
        'title': "Order Cancelled",
        'message': f"Hi {baker_shop_name}, we are sorry to inform you that order {order_id} has been cancelled by the customer.",
        'details': {
            'Order ID': order_id,
            'Status': 'Cancelled',
            'Reason': reason or "Cancelled by customer"
        },
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/baker/orders/",
        'action_text': "View Dashboard"
    }
    return send_premium_email(subject, 'emails/status_email.html', context, email)

def send_baker_custom_request_email(email, customer_name, baker_shop_name, custom_request):
    subject = f"New Custom Cake Request - HomeBaker"
    details = {
        'Customer': customer_name,
        'Request Type': custom_request.get_request_type_display(),
        'Flavor': custom_request.flavor or 'Not specified',
        'Status': 'Pending Review'
    }
    context = {
        'subject': subject,
        'status': 'Accepted',
        'title': "New Custom Request!",
        'message': f"Hi {baker_shop_name}, {customer_name} has sent you a new custom cake request.",
        'details': details,
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/baker/custom-requests/",
        'action_text': "Review Request"
    }
    return send_premium_email(subject, 'emails/status_email.html', context, email)

def send_baker_review_email(email, rating, comment, customer_name, baker_shop_name):
    subject = f"New {rating}-Star Review Received! - HomeBaker"
    context = {
        'subject': subject,
        'status': 'Accepted' if int(rating) >= 4 else 'Rejected',
        'title': "New Feedback!",
        'message': f"Hi {baker_shop_name}, {customer_name} has just reviewed their order.",
        'details': {
            'Rating': f"{rating} / 5 Stars",
            'Comment': comment or "No comment provided"
        },
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/profile/",
        'action_text': "View My Reviews"
    }
    return send_premium_email(subject, 'emails/status_email.html', context, email)

def send_ticket_resolved_email(email, customer_name, ticket_subject, ticket_id, resolution_message=None):
    subject = f"Support Ticket Resolved: #{ticket_id} - HomeBaker"
    full_message = f"Hello {customer_name}, we are happy to inform you that your support ticket regarding '{ticket_subject}' has been marked as resolved."
    if resolution_message:
        full_message += f"\n\nAdmin Message: {resolution_message}"
    context = {
        'subject': subject,
        'status': 'Accepted',
        'title': "Ticket Resolved",
        'message': full_message,
        'details': {
            'Ticket ID': f"#{ticket_id}",
            'Subject': ticket_subject,
            'Status': 'Resolved'
        },
        'footer_text': "We hope this resolves your concern.",
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/services/",
        'action_text': "View Services"
    }
    return send_premium_email(subject, 'emails/status_email.html', context, email)

def send_coupon_announcement(email, customer_name, coupon):
    subject = f"Special Offer! {coupon.discount_value}% OFF on Your Next Order - HomeBaker"
    context = {
        'subject': subject,
        'customer_name': customer_name,
        'coupon_code': coupon.code,
        'discount_value': coupon.discount_value,
        'min_order': coupon.min_order_amount,
        'valid_until': coupon.valid_until,
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/cakes/",
    }
    return send_premium_email(subject, 'emails/coupon_announcement.html', context, email)

def send_ultra_premium_letter(recipient_list, subject, content):
    context = {
        'subject': subject,
        'letter_content': content,
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/cakes/",
    }
    return send_premium_email(subject, 'emails/premium_letter.html', context, recipient_list)
