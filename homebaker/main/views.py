"""
Main Views - Consolidated imports from modular views
"""

# Import all views from modular files
from .views_auth import (
    login_view, logout_view, register, profile, remove_profile_picture,
    delete_account,
    verify_otp, resend_otp, send_login_otp, ajax_verify_fssai,
    delivery_dashboard, verify_delivery_otp, change_password
)
from .views_customer import (
    home, customer_home, cake_list, add_to_cart, cart, custom_cart, remove_from_cart, update_cart, checkout, order_tracking,
    my_orders, add_review, wallet, cancel_order, custom_cake, photo_custom_cake,
    submit_custom_request, my_custom_requests, cancel_custom_request, finalize_custom_request,
    verify_delivery, rate_order, mark_notification_read, mark_all_notifications_read,
    notifications_list, baker_public_profile, baker_reviews, services_index,
    about_us, faq, apply_coupon, subscribe_newsletter
)
from .views_baker import (
    baker_dashboard, baker_cakes, baker_add_cake, baker_edit_cake,
    baker_expenses, baker_delete_cake, manage_baker_orders, baker_accept_order,
    baker_custom_requests, respond_to_custom_request, trigger_delivery,
    baker_ai_analytics, baker_cancel_order
)
from .views_admin import (
    admin_dashboard, admin_users, admin_bakers, admin_approve_baker,
    admin_reject_baker, admin_suspend_user, admin_unsuspend_user,
    admin_block_user_temp,
    admin_audit_logs, admin_analytics,
    admin_revenue, admin_orders_list, admin_commission, admin_user_detail, admin_helpdesk,
    admin_coupons, admin_delete_coupon,
    admin_letterbox, admin_send_letter
)
