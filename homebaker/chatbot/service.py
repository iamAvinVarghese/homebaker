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
You are Ammini AI, a helpful virtual assistant for the "Home Baker Cake Ordering & Management System".
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
- You cannot access real-time database records (like specific order status or user account details) directly yet. 
- Ask users to check their "My Orders" page for status.
"""

    @classmethod
    def get_response(cls, message, history=None):
        """
        Get a response from Gemini API.
        
        Args:
            message (str): The user's message.
            history (list): List of previous messages in format [{'role': 'user', 'parts': ['msg']}, {'role': 'model', 'parts': ['msg']}]
        
        Returns:
            str: The AI's response.
        """
        try:
            model = cls.get_model()
            if not model:
                return "I'm currently offline. Please check the system configuration (API Key missing)."

            # Prepare chat session with history
            chat = model.start_chat(history=history or [])
            
            response = chat.send_message(message)
            
            # Robust check for response text (handles safety blocks)
            if response.candidates and response.candidates[0].content.parts:
                return response.text
            else:
                logger.warning(f"Gemini hidden/blocked response: {response.prompt_feedback}")
                return "I'm sorry, I cannot respond to that message due to safety guidelines. How else can I help you with your bakery queries?"
            
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again later."
