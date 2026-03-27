import os
import django
import google.generativeai as genai
import PIL.Image
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

def test_ocr():
    print("--- Testing OCR with Gemini 2.5-flash ---")
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    
    # Use a sample image
    img_path = r'd:\HomeBakerProject\homebaker\media\baker_documents\fssai.webp'
    print(f"Loading image: {img_path}")
    img = PIL.Image.open(img_path)
    
    prompt = """
    Extract the FSSAI License Number or Registration Number from this certificate.
    - We are looking for: a 9-character code (6 letters + 3 numbers)
    - If you see a code like this, return JUST that code with no other text.
    - It might also be a 14-digit standard number.
    """
    
    try:
        print("Sending request to Gemini...")
        response = model.generate_content([prompt, img])
        print("Response received!")
        print(f"Full response object: {response}")
        try:
            print(f"Text output: {response.text}")
        except Exception as text_err:
            print(f"Error accessing .text: {text_err}")
            print(f"Prompt feedback: {response.prompt_feedback}")
            print(f"Candidates status: {[c.finish_reason for c in response.candidates] if response.candidates else 'No candidates'}")
            
    except Exception as e:
        print(f"General error: {e}")

if __name__ == "__main__":
    test_ocr()
