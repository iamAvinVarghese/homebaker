import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ChatbotService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            api_key = settings.GEMINI_API_KEY
            if not api_key:
                logger.warning("GEMINI_API_KEY is not set.")
                return None
            
            try:
                genai.configure(api_key=api_key)
                cls._model = genai.GenerativeModel(
                    model_name='models/gemini-2.5-flash',
                    system_instruction=cls.get_system_prompt()
                )
            except Exception as e:
                logger.error(f"Failed to initialize Gemini model: {e}")
                return None
            
        return cls._model

    @staticmethod
    def get_system_prompt():
        return """
You are Ana AI, a helpful virtual assistant for the "Home Baker Cake Ordering & Management System".
Your goal is to assist customers, bakers, and admins with their queries.

ROLE & TONE:
- Be polite, concise, professional, and friendly.
- Use a business-friendly tone.
- Never provide false information. If you don't know something, say "I don't have that information right now."

CAPABILITIES:
1. Customer Support:
   - Explain how to register, login, and place orders.
   - Explain that delivery is handled by bakers.
   - Refunds are processed by admins upon request.
   - **Order Tracking**: You can now track orders if the user provides an Order ID (e.g., #12345).

2. Baker Support:
   - Explain how to register as a baker (choose 'Baker' role during signup).
   - Provide general sales tips (e.g., "High-quality photos attract more customers").
   - Explain dashboard features (managing cakes, orders, expenses).

3. Admin Support:
   - Explain that admins approve bakers and manage users.

CONTEXT:
- The platform connects home bakers with customers.
- Users verify email via OTP (though currently simplified/disabled for dev).
- Payments are made via the Wallet only.

LIMITATIONS:
- For specific account changes, refer users to their Profile or Settings pages.
"""

    @classmethod
    def get_response(cls, message, history=None, user=None):
        """
        Get a response from Gemini API, with optional order tracking logic.
        """
        import re
        from main.models import Order
        
        # 1. Check for Order ID pattern (e.g. #12345 or 12345)
        order_match = re.search(r'#?(\d{5})', message)
        
        if order_match:
            order_id_num = order_match.group(1)
            full_order_id = f"#{order_id_num}"
            
            try:
                # If user is logged in, restrict tracking to their own orders for security
                # Unless they are an admin or baker of that order
                order = None
                if user and user.is_authenticated:
                    if user.is_staff:
                        order = Order.objects.filter(order_id=full_order_id).first()
                    elif user.profile.role == 'baker':
                        order = Order.objects.filter(order_id=full_order_id, items__cake__baker=user).first()
                    else:
                        order = Order.objects.filter(order_id=full_order_id, customer=user).first()
                
                if order:
                    status_display = order.get_status_display()
                    delivery_date = order.delivery_date.strftime('%d %b %Y')
                    
                    tracking_response = f"I've found your order **{full_order_id}**! \n\n"
                    tracking_response += f"📍 **Status:** {status_display}\n"
                    tracking_response += f"📅 **Delivery Date:** {delivery_date}\n\n"
                    
                    if order.status == 'pending':
                        tracking_response += "Your order has been placed and is currently awaiting baker confirmation. 🧁"
                    elif order.status == 'confirmed':
                        tracking_response += "Great news! The baker has confirmed your order and will start preparation soon. ✨"
                    elif order.status == 'baking':
                        tracking_response += "Your cake is currently in the oven! The baker is working their magic. 👨‍🍳"
                    elif order.status == 'packing':
                        tracking_response += "Your order is being beautifully packed and prepared for transit. 🎀"
                    elif order.status == 'out_for_delivery':
                        tracking_response += "Your delicious treats are on the way! Please keep your phone handy. 🚚"
                    elif order.status == 'delivered':
                        tracking_response += "This order was delivered on " + (order.delivered_at.strftime('%d %b') if order.delivered_at else 'schedule') + ". We hope you enjoyed it! 🥳"
                    elif order.status == 'cancelled':
                        tracking_response += "I'm sorry, but this order has been cancelled. Please contact support if you have questions."
                        
                    return tracking_response
                elif not user or not user.is_authenticated:
                    return "I've detected an Order ID, but you need to be **logged in** to track your order details for security reasons. Please log in and try again!"
                else:
                    return f"I couldn't find an order with the ID **{full_order_id}** associated with your account. Please double-check the ID and try again."
            except Exception as e:
                logger.error(f"Order Tracking Error: {e}")
                # Fall back to AI response if database check fails
        
        # 2. Regular AI Response
        try:
            model = cls.get_model()
            if not model:
                return "I'm currently offline. Please check the system configuration (API Key missing)."

            # Prepare chat session with history
            chat = model.start_chat(history=history or [])
            
            response = chat.send_message(message)
            
            # Robust check for response text
            if response.candidates and response.candidates[0].content.parts:
                return response.text
            else:
                return "I'm sorry, I cannot respond to that message due to safety guidelines. How else can I help you with your bakery queries?"
            
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again later."
