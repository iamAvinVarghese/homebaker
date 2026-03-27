# from django.contrib import admin
from django.urls import path, include
from main.views import (
    # Public & Customer
    home, customer_home, cake_list, add_to_cart, cart, custom_cart, remove_from_cart, update_cart, checkout, order_tracking,
    my_orders, add_review, wallet, cancel_order, custom_cake, photo_custom_cake,
    submit_custom_request, my_custom_requests, cancel_custom_request, finalize_custom_request,
    
    # NEW
    mark_notification_read, mark_all_notifications_read, notifications_list,
    baker_public_profile, baker_reviews, services_index,
    about_us, faq, apply_coupon,


    # Auth
    login_view, logout_view, register, profile, remove_profile_picture,
    delete_account,
    verify_otp, resend_otp, send_login_otp, ajax_verify_fssai,
    delivery_dashboard, verify_delivery_otp, change_password,
    # Baker
    baker_dashboard, baker_cakes, baker_add_cake, baker_edit_cake,
    baker_expenses, baker_delete_cake, manage_baker_orders, baker_accept_order,
    baker_custom_requests, respond_to_custom_request,
    baker_ai_analytics, baker_cancel_order,
    
    # Admin
    admin_dashboard, admin_users, admin_bakers, admin_approve_baker,
    admin_reject_baker, admin_suspend_user, admin_unsuspend_user,
    admin_block_user_temp,
    admin_audit_logs, admin_analytics,
    admin_revenue, admin_orders_list, admin_commission, admin_user_detail, admin_helpdesk,
    admin_coupons, admin_delete_coupon,
    
    # Delivery
    trigger_delivery, verify_delivery, rate_order
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin removed
    # path('admin/', admin.site.urls),
    
    # Chatbot
    path('chatbot/', include('chatbot.urls')),


    # ========== PUBLIC PAGES ==========
    path('', home, name='home'),
    path('customer-home/', customer_home, name='customer_home'),
    path('cakes/', cake_list, name='cakes'),
    path('custom-cake/', custom_cake, name='custom_cake'),
    path('photo-custom-cake/', photo_custom_cake, name='photo_custom_cake'),
    path('baker/<int:baker_id>/', baker_public_profile, name='baker_public_profile'),
    path('baker/<int:baker_id>/reviews/', baker_reviews, name='baker_reviews'),
    path('about-us/', about_us, name='about_us'),
    path('faq/', faq, name='faq'),

    # ========== AUTHENTICATION ==========
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register, name='register'),
    path('profile/', profile, name='profile'),
    path('profile/remove-picture/', remove_profile_picture, name='remove_profile_picture'),
    path('profile/delete/', delete_account, name='delete_account'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('resend-otp/', resend_otp, name='resend_otp'),
    path('send-login-otp/', send_login_otp, name='send_login_otp'),
    path('profile/password/', change_password, name='change_password'),


    # ========== CUSTOMER MODULE ==========
    path('cart/add/<int:cake_id>/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:cake_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:cake_id>/', update_cart, name='update_cart'),
    path('cart/', cart, name='cart'),
    path('custom-cart/', custom_cart, name='custom_cart'),
    path('checkout/', checkout, name='checkout'),
    path('apply-coupon/', apply_coupon, name='apply_coupon'),
    path('order-tracking/<str:order_id>/', order_tracking, name='order_tracking'),
    path('my-orders/', my_orders, name='my_orders'),
    path('notifications/', notifications_list, name='notifications'),
    path('mark-notification-read/<int:notification_id>/', mark_notification_read, name='mark_notification_read'),
    path('mark-all-notifications-read/', mark_all_notifications_read, name='mark_all_notifications_read'),
    path('my-custom-requests/', my_custom_requests, name='my_custom_requests'),

    path('review/<str:order_id>/', add_review, name='add_review'),


    path('wallet/', wallet, name='wallet'),
    path('orders/<str:order_id>/cancel/', cancel_order, name='cancel_order'),
    path('custom-requests/<int:request_id>/cancel/', cancel_custom_request, name='cancel_custom_request'),
    path('custom-requests/<int:request_id>/finalize/', finalize_custom_request, name='finalize_custom_request'),
    
    path('services/', services_index, name='services'),

    # ========== BAKER MODULE ==========
    path('baker/dashboard/', baker_dashboard, name='baker_dashboard'),
    path('baker/cakes/', baker_cakes, name='baker_cakes'),
    path('baker/cakes/add/', baker_add_cake, name='baker_add_cake'),
    path('baker/cakes/<int:cake_id>/edit/', baker_edit_cake, name='baker_edit_cake'),
    path('baker/expenses/', baker_expenses, name='baker_expenses'),
    path('baker/orders/', manage_baker_orders, name='baker_orders'),
    path('baker/ai-analytics/', baker_ai_analytics, name='baker_ai_analytics'),
    path('baker/custom-requests/', baker_custom_requests, name='baker_custom_requests'),
    path('baker/custom-requests/<int:request_id>/respond/', respond_to_custom_request, name='respond_to_custom_request'),
    path('submit-custom-request/', submit_custom_request, name='submit_custom_request'),

    path('baker/orders/<int:order_id>/accept/', baker_accept_order, name='baker_accept_order'),
    path('baker/orders/<int:order_id>/deliver/', trigger_delivery, name='trigger_delivery'),
    path('baker/orders/<int:order_id>/cancel/', baker_cancel_order, name='baker_cancel_order'),
    path('baker/cakes/<int:cake_id>/delete/', baker_delete_cake, name='baker_delete_cake'),
    
    # ========== DELIVERY & RATING ==========
    path('verify-delivery/<str:order_id>/', verify_delivery, name='verify_delivery'),
    path('rate-order/<str:order_id>/', rate_order, name='rate_order'),
    path('delivery/dashboard/', delivery_dashboard, name='delivery_dashboard'),
    path('delivery/verify-otp/', verify_delivery_otp, name='verify_delivery_otp'),

    # ========== ADMIN MODULE ==========
    path('admin-panel/', admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', admin_users, name='admin_users'),
    path('admin-panel/bakers/', admin_bakers, name='admin_bakers'),
    path('admin-panel/bakers/<int:baker_id>/approve/', admin_approve_baker, name='admin_approve_baker'),
    path('admin-panel/bakers/<int:baker_id>/reject/', admin_reject_baker, name='admin_reject_baker'),
    path('admin-panel/users/<int:user_id>/suspend/', admin_suspend_user, name='admin_suspend_user'),
    path('admin-panel/users/<int:user_id>/block-temp/', admin_block_user_temp, name='admin_block_user_temp'),
    path('admin-panel/users/<int:user_id>/unsuspend/', admin_unsuspend_user, name='admin_unsuspend_user'),
    path('admin-panel/audit-logs/', admin_audit_logs, name='admin_audit_logs'),
    path('admin-panel/analytics/', admin_analytics, name='admin_analytics'),
    path('admin-panel/revenue/', admin_revenue, name='admin_revenue'),
    path('admin-panel/orders-list/', admin_orders_list, name='admin_orders_list'),
    path('admin-panel/commission/', admin_commission, name='admin_commission'),
    path('admin-panel/users/<int:user_id>/detail/', admin_user_detail, name='admin_user_detail'),
    path('admin-panel/helpdesk/', admin_helpdesk, name='admin_helpdesk'),
    path('admin-panel/coupons/', admin_coupons, name='admin_coupons'),
    path('admin-panel/coupons/<int:coupon_id>/delete/', admin_delete_coupon, name='admin_delete_coupon'),
    path('ajax-verify-fssai/', ajax_verify_fssai, name='ajax_verify_fssai'),
]

# Media files (for development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None)
