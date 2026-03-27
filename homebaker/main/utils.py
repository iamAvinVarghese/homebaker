from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

def send_otp_email(email, otp, purpose="registration"):
    """
    Send OTP via Django's email backend (configured for SendGrid in settings)
    purpose: "registration" or "login"
    """
    subject = f"Your {purpose.capitalize()} OTP - HomeBaker"
    
    # Render HTML content using template
    context = {
        'subject': subject,
        'purpose': purpose.capitalize(),
        'otp': otp,
    }
    html_content = render_to_string('emails/otp_email.html', context)
    message_text = strip_tags(html_content)
    
    try:
        print(f"DEBUG: Attempting to send email to {email} via configured backend...")
        
        # Use Django's send_mail - it will use sendgrid_backend if configured
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        
        print(f"DEBUG: Email sent successfully to {email}")
        logger.info(f"OTP email sent to {email}")
        return True
    except Exception as e:
        print(f"DEBUG: ERROR sending OTP email: {e}")
        logger.error(f"Error sending OTP email: {e}")
        
        # Log to file for debugging
        return False
        
def send_delivery_otp_email(email, otp, order_id, customer_name):
    """
    Send Delivery OTP email to the customer.
    """
    subject = f"Order {order_id} is Ready for Pickup - HomeBaker"
    
    context = {
        'subject': subject,
        'purpose': "Delivery Confirmation",
        'otp': otp,
        'customer_name': customer_name,
        'order_id': order_id,
        'is_delivery': True,
    }
    
    html_content = render_to_string('emails/otp_email.html', context)
    message_text = strip_tags(html_content)
    
    try:
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Delivery OTP email sent to {email} for Order {order_id}")
        return True
    except Exception as e:
        logger.error(f"Error sending delivery OTP email: {e}")
        return False

def send_approval_email(email, is_approved, shop_name):
    """
    Send approval or rejection email to the baker.
    """
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
    
    html_content = render_to_string('emails/status_email.html', context)
    message_text = strip_tags(html_content)
        
    try:
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Approval status email ({status}) sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending approval email: {e}")
        return False

def send_custom_request_status_email(email, status, cake_name, baker_name, baker_message, price_quote=None):
    """
    Send custom cake request status update email to the customer.
    """
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
    
    html_content = render_to_string('emails/status_email.html', context)
    message_text = strip_tags(html_content)
        
    try:
        print(f"DEBUG: Attempting to send custom request {status} email to {email}...")
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        print(f"DEBUG: Custom request email sent successfully to {email}")
        logger.info(f"Custom request {status} email sent to {email}")
        return True
    except Exception as e:
        print(f"DEBUG: ERROR sending custom request email: {e}")
        logger.error(f"Error sending custom request email: {e}")
        return False

def send_delivery_thank_you_email(email, order_id, customer_name):
    """
    Send a thank-you email after successful delivery.
    """
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
    
    html_content = render_to_string('emails/order_details_email.html', context)
    message_text = strip_tags(html_content)
    
    try:
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Delivery thank-you email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending thank-you email: {e}")
        return False

def send_order_placed_email(email, order, customer_name):
    """
    Send an order placement confirmation email to the customer.
    """
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
    
    html_content = render_to_string('emails/order_details_email.html', context)
    message_text = strip_tags(html_content)
    
    try:
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Order placed email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending order placed email: {e}")
        return False

def send_baker_delivery_notification_email(email, order_id, baker_shop_name, payout_amount):
    """
    Send an email to the baker when a delivery assistant completes a delivery.
    """
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
    
    html_content = render_to_string('emails/status_email.html', context)
    message_text = strip_tags(html_content)
    
    try:
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Baker delivery notification email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending baker delivery notification email: {e}")
        return False

def send_order_acceptance_email(email, order_id, customer_name, baker_shop_name):
    """
    Send an email to the customer when a baker accepts their order.
    No OTP is included in this email.
    """
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
    
    html_content = render_to_string('emails/status_email.html', context)
    message_text = strip_tags(html_content)
    
    try:
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Order acceptance email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending order acceptance email: {e}")
        return False
        
def send_baker_new_order_email(email, order, baker_shop_name):
    """
    Send an email to the baker when a new order is received.
    """
    subject = f"New Order Received {order.order_id} - HomeBaker"
    
    # Filter items that belong to this baker
    baker_items = order.items.filter(cake__baker__email=email)
    baker_subtotal = sum(item.subtotal for item in baker_items)
    
    items_details = []
    for item in baker_items:
        detail = f"{item.cake.name} - {item.quantity}kg"
        if item.cake.flavor:
            detail += f" (Flavor: {item.cake.flavor})"
        if item.message_on_cake:
            detail += f" - Message: \"{item.message_on_cake}\""
        items_details.append(detail)
    
    items_text = "\n".join(items_details) if items_details else "Check dashboard for details"

    context = {
        'subject': subject,
        'status': 'Accepted',
        'title': "New Order Received!",
        'message': f"Hi {baker_shop_name}, you have received a new order {order.order_id}. Here are the items for you to prepare:",
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
    
    html_content = render_to_string('emails/status_email.html', context)
    message_text = strip_tags(html_content)
    
    try:
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Baker new order email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending baker new order email: {e}")
        return False

def send_baker_order_cancelled_email(email, order_id, baker_shop_name, reason=None):
    """
    Send an email to the baker when an order is cancelled by the customer.
    """
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
    
    html_content = render_to_string('emails/status_email.html', context)
    message_text = strip_tags(html_content)
    
    try:
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Baker order cancellation email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending baker order cancellation email: {e}")
        return False

def send_baker_custom_request_email(email, customer_name, baker_shop_name, custom_request):
    """
    Send an email to the baker when a new custom cake request is received.
    """
    subject = f"New Custom Cake Request - HomeBaker"
    
    details = {
        'Customer': customer_name,
        'Request Type': custom_request.get_request_type_display(),
        'Flavor': custom_request.flavor or 'Not specified',
        'Size/Weight': custom_request.size or 'Not specified',
        'Status': 'Pending Review'
    }

    # Add extra specs if available
    if custom_request.specs:
        if custom_request.specs.get('message_on_cake'):
            details['Message on Cake'] = custom_request.specs.get('message_on_cake')
        if custom_request.specs.get('extra_instructions'):
            details['Extra Instructions'] = custom_request.specs.get('extra_instructions')
        if custom_request.specs.get('occasion'):
            details['Occasion'] = custom_request.specs.get('occasion')

    context = {
        'subject': subject,
        'status': 'Accepted',
        'title': "New Custom Request!",
        'message': f"Hi {baker_shop_name}, {customer_name} has sent you a new custom cake request. Please review and provide a quote.",
        'details': details,
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/baker/custom-requests/",
        'action_text': "Review Request"
    }
    
    html_content = render_to_string('emails/status_email.html', context)
    message_text = strip_tags(html_content)
    
    try:
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Baker custom request email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending baker custom request email: {e}")
        return False

def send_baker_review_email(email, rating, comment, customer_name, baker_shop_name):
    """
    Send an email to the baker when a new review is received.
    """
    subject = f"New {rating}-Star Review Received! - HomeBaker"
    
    context = {
        'subject': subject,
        'status': 'Accepted' if int(rating) >= 4 else 'Rejected' if int(rating) <= 2 else 'Accepted',
        'title': "New Feedback!",
        'message': f"Hi {baker_shop_name}, {customer_name} has just reviewed their order.",
        'details': {
            'Rating': f"{rating} / 5 Stars",
            'Comment': comment or "No comment provided"
        },
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/profile/",
        'action_text': "View My Reviews"
    }
    
    html_content = render_to_string('emails/status_email.html', context)
    message_text = strip_tags(html_content)
    
    try:
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Baker review email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending baker review email: {e}")
        return False

def send_ticket_resolved_email(email, customer_name, ticket_subject, ticket_id, resolution_message=None):
    """
    Send a professional email to the customer when their support ticket is resolved.
    """
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
        'footer_text': "We hope this resolves your concern. If you have any further questions, please feel free to reach out to us again.",
        'action_url': f"{settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'}/services/",
        'action_text': "View Services"
    }
    
    html_content = render_to_string('emails/status_email.html', context)
    message_text = strip_tags(html_content)
    
    try:
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Ticket resolution email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending ticket resolution email: {e}")
        return False
def send_coupon_announcement(email, customer_name, coupon):
    """
    Send a professional coupon announcement email to the customer.
    """
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
    
    html_content = render_to_string('emails/coupon_announcement.html', context)
    message_text = strip_tags(html_content)
    
    try:
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Coupon announcement email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending coupon announcement email: {e}")
        return False
