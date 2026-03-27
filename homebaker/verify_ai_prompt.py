import os
import django
import sys
import json

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from main.ai_utils import CakeDesigner

def verify_ai_prompt():
    print("--- Verifying AI Prompt Engineering ---")
    
    requirements = {
        'flavor': 'Red Velvet',
        'shape': 'Heart',
        'size': '2kg',
        'design_style': 'Modern Minimalist',
        'primary_colors': 'Deep Red and Gold',
        'message_on_cake': 'Happy Anniversary Raju!',
        'extra_instructions': 'Add some gold leaf accents and edible flowers.'
    }
    
    print(f"Testing with message: {requirements['message_on_cake']}")
    
    # We only want to see the Gemini part, so we'll mock the requirements if needed 
    # but generate_custom_design calls Gemini first.
    # Note: This requires a valid GEMINI_API_KEY in settings.
    
    try:
        # result = CakeDesigner.generate_custom_design(requirements)
        # We manually call the Gemini part from inside generate_custom_design logic
        # but for simplicity, we let it run but we can mock the request part if we want.
        # Actually, let's just let it run but we only care about the print statements.
        
        from django.conf import settings
        import google.generativeai as genai
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # This is the exact prompt from ai_utils.py
        designer_prompt = f"""
            Act as an expert luxury cake designer and professional prompt engineer for AI image generators (Stable Diffusion/Leonardo.ai).
            
            I will give you cake requirements, and you will provide three things:
            1. A highly descriptive photographic prompt for Leonardo.ai. 
               - CRITICAL: If a "Message on Cake" is provided, you MUST describe exactly how it appears (e.g., "elegant cursive gold calligraphy", "neatly piped chocolate lettering", "playful bold font") and where it is placed (e.g., "centered on the top surface", "elegantly written on the side of the bottom tier").
               - Focus on realistic textures (moist cake, creamy frosting), lighting (warm studio lighting), and professional food photography composition.
            2. Professional step-by-step design instructions for a human baker.
            3. A short, appealing title/summary for the design.

            Requirements:
            - Flavor: {requirements.get('flavor')}
            - Shape: {requirements.get('shape')}
            - Size: {requirements.get('size')}
            - Style: {requirements.get('design_style')}
            - Colors: {requirements.get('primary_colors')}
            - Message on Cake: "{requirements.get('message_on_cake', 'None')}"
            - Extra: {requirements.get('extra_instructions')}

            Rules:
            - Return ONLY a valid JSON object.
            - Keys MUST be: "image_prompt", "design_instructions", "summary".
            - No markdown blocks. No conversational filler.
            """
            
        print("\n--- SENDING PROMPT TO GEMINI ---")
        response = model.generate_content(designer_prompt)
        text = response.text.strip()
        print(f"RAW RESPONSE: {text}")
        
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            enriched_data = json.loads(json_match.group(0))
            image_prompt = enriched_data.get('image_prompt', '')
            print("\n--- GENERATED IMAGE PROMPT ---")
            print(image_prompt)
            
            if 'anniversary' in image_prompt.lower() and 'raju' in image_prompt.lower():
                print("\n[VERIFIED] The message was successfully included in the prompt.")
            else:
                print("\n[WARNING] The message was NOT found in the prompt.")
        else:
            print("\n[ERROR] Could not parse JSON from Gemini response.")
            
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")

if __name__ == "__main__":
    verify_ai_prompt()
