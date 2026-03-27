from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging
from .service import ChatbotService

logger = logging.getLogger(__name__)

@require_POST
def chat_api(request):
    """
    API endpoint for the chatbot.
    Expects JSON payload: {"message": "user message", "history": []}
    """
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        history = data.get('history', [])
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
            
        # Get AI response
        response_text = ChatbotService.get_response(message, history)
        
        return JsonResponse({
            'response': response_text
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Chat API Error: {e}")
        return JsonResponse({'error': 'Internal Server Error'}, status=500)
