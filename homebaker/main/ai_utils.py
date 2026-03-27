"""
AI & Analytics Utilities for Home Baker System
Includes: Recommendation Engine, Smart Pricing, Business Insights, Predictions
"""

from django.db.models import Q, Count, Sum, Avg, F, DecimalField
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import statistics
import google.generativeai as genai
from django.conf import settings
from .models import Cake, Order, OrderItem, Review, Expense, BakerProfile, Wallet


class RecommendationEngine:
    """AI-based cake recommendation system"""
    
    @staticmethod
    def get_recommendations_for_user(user, limit=5):
        """Get personalized cake recommendations for a user"""
        recommendations = []
        
        # 1. Based on order history
        user_orders = Order.objects.filter(customer=user, status='delivered')
        if user_orders.exists():
            # Get flavors and occasions from user's past orders
            ordered_cakes = Cake.objects.filter(
                order_items__order__in=user_orders
            ).distinct()
            
            # Find similar cakes
            if ordered_cakes.exists():
                flavors = ordered_cakes.values_list('flavor', flat=True).distinct()
                occasions = ordered_cakes.values_list('occasion', flat=True).distinct()
                
                similar_cakes = Cake.objects.filter(
                    Q(flavor__in=flavors) | Q(occasion__in=occasions),
                    is_available=True
                ).exclude(
                    id__in=ordered_cakes.values_list('id', flat=True)
                ).distinct()[:limit]
                
                recommendations.extend(similar_cakes)
        
        # 2. Based on ratings (popular cakes)
        if len(recommendations) < limit:
            popular_cakes = Cake.objects.filter(
                is_available=True,
                average_rating__gte=4.0
            ).order_by('-average_rating', '-order_count')[:limit]
            
            for cake in popular_cakes:
                if cake not in recommendations:
                    recommendations.append(cake)
        
        # 3. Trending cakes (recent orders)
        if len(recommendations) < limit:
            trending_cakes = Cake.objects.filter(
                is_available=True
            ).annotate(
                recent_orders=Count('order_items', filter=Q(
                    order_items__order__created_at__gte=timezone.now() - timedelta(days=7)
                ))
            ).order_by('-recent_orders', '-order_count')[:limit]
            
            for cake in trending_cakes:
                if cake not in recommendations:
                    recommendations.append(cake)
        
        # 4. Fill with available cakes if still needed
        if len(recommendations) < limit:
            available_cakes = Cake.objects.filter(
                is_available=True
            ).exclude(
                id__in=[c.id for c in recommendations]
            ).order_by('-created_at')[:limit - len(recommendations)]
            
            recommendations.extend(available_cakes)
        
        return recommendations[:limit]
    
    @staticmethod
    def get_trending_cakes(limit=5, baker=None, require_orders=False):
        """Get trending cakes based on recent orders"""
        qs = Cake.objects.filter(is_available=True)
        if baker:
            qs = qs.filter(baker=baker)
            
        qs = qs.annotate(
            recent_orders=Count('order_items', filter=Q(
                order_items__order__created_at__gte=timezone.now() - timedelta(days=7)
            ))
        )
        if require_orders:
            qs = qs.filter(recent_orders__gt=0)
            
        return qs.order_by('-recent_orders', '-average_rating')[:limit]


class SmartPricing:
    """Smart pricing suggestions based on analytics"""
    
    @staticmethod
    def suggest_price(cake, base_price=None):
        """Suggest optimal price for a cake"""
        if base_price is None:
            base_price = cake.price
        
        # Get similar cakes
        similar_cakes = Cake.objects.filter(
            Q(flavor=cake.flavor) | Q(occasion=cake.occasion),
            is_available=True
        ).exclude(id=cake.id)
        
        if similar_cakes.exists():
            avg_price = similar_cakes.aggregate(Avg('price'))['price__avg']
            if avg_price:
                # Suggest price within 10% of average
                suggested_price = avg_price * Decimal('1.05')  # 5% above average
                return {
                    'suggested_price': round(suggested_price, 2),
                    'market_average': round(avg_price, 2),
                    'current_price': float(base_price),
                    'recommendation': 'increase' if base_price < avg_price else 'decrease'
                }
        
        return {
            'suggested_price': float(base_price),
            'market_average': None,
            'current_price': float(base_price),
            'recommendation': 'maintain'
        }
    


class BusinessInsights:
    """Generate business insights and analytics"""
    
    @staticmethod
    def get_revenue_analytics(baker=None, days=30):
        # Calculate last 6 months of revenue
        labels = []
        actual_data = []
        from datetime import date
        today = timezone.now().date()
        
        for i in range(5, -1, -1):
            target_month = today.month - i
            target_year = today.year
            while target_month <= 0:
                target_month += 12
                target_year -= 1
                
            month_label = date(target_year, target_month, 1).strftime('%b')
            labels.append(month_label)
            
            qs = Order.objects.filter(
                created_at__year=target_year,
                created_at__month=target_month,
                payment_status='paid',
                status='delivered'
            )
            if baker:
                qs = qs.filter(items__cake__baker=baker)
                
            rev = qs.aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
            actual_data.append(float(rev))
            
        # Basic prediction based on recent growth
        if len(actual_data) >= 2 and actual_data[-2] > 0:
            growth = (actual_data[-1] - actual_data[-2]) / actual_data[-2]
            # Cap growth prediction at 20% to avoid extreme outliers
            growth = max(-0.2, min(0.2, growth)) 
            predicted_value = actual_data[-1] * (1 + growth)
        else:
            predicted_value = actual_data[-1] * 1.05 # Default 5% default growth if not enough data
            
        next_month = today.month + 1
        predicted_label = date(today.year if next_month <= 12 else today.year + 1, next_month if next_month <= 12 else 1, 1).strftime('%b (Pred)')
        
        return {
            'total_revenue': sum(actual_data),
            'period_days': days,
            'monthly_breakdown': [],
            'labels': labels,
            'data': actual_data,
            'predicted_value': predicted_value,
            'predicted_label': predicted_label
        }
    
    @staticmethod
    def get_profit_analytics(baker, days=30):
        """Calculate profit after expenses and commission"""
        start_date = timezone.now() - timedelta(days=days)
        
        # Get revenue
        orders = Order.objects.filter(
            items__cake__baker=baker,
            created_at__gte=start_date,
            payment_status='paid',
            status='delivered'
        ).distinct()
        
        revenue = orders.aggregate(
            total=Sum('subtotal')
        )['total'] or Decimal('0.00')
        
        # Calculate commission
        baker_profile = BakerProfile.objects.get(user_profile__user=baker)
        commission = revenue * (baker_profile.commission_rate / 100)
        
        # Calculate expenses (40% of Revenue - Commission)
        expenses = (revenue - commission) * Decimal('0.40')
        
        # Calculate profit
        profit = revenue - expenses - commission
        
        return {
            'revenue': float(revenue),
            'expenses': float(expenses),
            'commission': float(commission),
            'profit': float(profit),
            'profit_margin': float((profit / revenue * 100) if revenue > 0 else 0),
            'period_days': days
        }
    
    @staticmethod
    def get_growth_prediction(baker=None, days=30):
        """Real growth prediction based on recent trends"""
        now = timezone.now()
        current_period_start = now - timedelta(days=days)
        previous_period_start = current_period_start - timedelta(days=days)
        
        # Current period revenue
        qs_current = Order.objects.filter(
            created_at__gte=current_period_start,
            created_at__lte=now,
            payment_status='paid',
            status='delivered'
        )
        if baker:
            qs_current = qs_current.filter(items__cake__baker=baker)
        current_revenue = qs_current.aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
        
        # Previous period revenue
        qs_previous = Order.objects.filter(
            created_at__gte=previous_period_start,
            created_at__lt=current_period_start,
            payment_status='paid',
            status='delivered'
        )
        if baker:
            qs_previous = qs_previous.filter(items__cake__baker=baker)
        previous_revenue = qs_previous.aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
        
        current_revenue = float(current_revenue)
        previous_revenue = float(previous_revenue)
        
        if previous_revenue > 0:
            growth_rate = ((current_revenue - previous_revenue) / previous_revenue) * 100
        else:
            growth_rate = 100.0 if current_revenue > 0 else 0.0
            
        # Predict next period based on trend
        predicted_growth = max(-20.0, min(50.0, growth_rate)) # Limit wild swings
        predicted_next_period = current_revenue * (1 + (predicted_growth / 100))
        
        return {
            'recent_revenue': current_revenue,
            'previous_revenue': previous_revenue,
            'growth_rate': growth_rate,
            'predicted_growth': predicted_growth,
            'predicted_next_period': predicted_next_period,
            'trend': 'increasing' if growth_rate > 0 else 'decreasing' if growth_rate < 0 else 'stable'
        }
    
    @staticmethod
    def get_demand_prediction(cake, days=7):
        """Predict demand for a cake based on historical data"""
        # Get historical orders for this cake
        historical_orders = OrderItem.objects.filter(
            cake=cake,
            order__created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        if historical_orders.exists():
            # Calculate average orders per week
            weekly_avg = historical_orders.count() / 4  # Approximate weeks
            predicted_demand = weekly_avg * (days / 7)
            
            return {
                'predicted_orders': round(predicted_demand, 1),
                'confidence': 'high' if historical_orders.count() > 10 else 'medium' if historical_orders.count() > 5 else 'low',
                'historical_orders': historical_orders.count()
            }
        
        return {
            'predicted_orders': 0,
            'confidence': 'low',
            'historical_orders': 0
        }
    
    @staticmethod
    def generate_insights(baker=None):
        """Generate automatic AI business insights based on real data using Gemini"""
        import google.generativeai as genai
        from django.conf import settings
        import json
        
        insights = []
        
        # Collect Real Data
        revenue_data = BusinessInsights.get_revenue_analytics(baker, days=30)
        profit_data = BusinessInsights.get_profit_analytics(baker, days=30) if baker else {'profit': 0, 'margin': 0}
        growth_data = BusinessInsights.get_growth_prediction(baker, days=30)
        trending = RecommendationEngine.get_trending_cakes(limit=3, baker=baker, require_orders=True)
        trending_data = list(trending.values('name', 'recent_orders')) if trending.exists() else []
        
        # Determine fallback default behavior if API fails
        def get_fallback_insights():
            fallback = []
            if revenue_data['total_revenue'] > 0:
                fallback.append({
                    'type': 'revenue',
                    'message': f"Total revenue in last 30 days: ₹{revenue_data['total_revenue']:,.2f}",
                    'priority': 'info'
                })
            if baker and profit_data.get('profit', 0) > 0:
                fallback.append({
                    'type': 'profit',
                    'message': f"Profit increased by ₹{profit_data.get('profit', 0):,.2f}",
                    'priority': 'success'
                })
            else:
                fallback.append({
                    'type': 'profit',
                    'message': "No clear profit trend yet. Keep promoting your cakes!",
                    'priority': 'info'
                })
            if growth_data['growth_rate'] > 0:
                fallback.append({
                    'type': 'growth',
                    'message': f"Revenue growth: {growth_data['growth_rate']:.1f}% - Excellent performance!",
                    'priority': 'success'
                })
            if trending.exists():
                fallback.append({
                    'type': 'trending',
                    'message': f"{trending.count()} of your cake(s) are trending this week",
                    'priority': 'success'
                })
            return fallback

        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            
            prompt = f"""
            You are an expert AI business analyst for a home baker. Analyze this 30-day performance data and provide 3 to 4 actionable, encouraging, and highly specific business insights.
            
            Real Bakery Data:
            - Total Revenue: ₹{revenue_data.get('total_revenue', 0)}
            - Orders Completed: {revenue_data.get('order_count', 0)}
            - Profit Margin: {profit_data.get('profit_margin', 0)}%
            - Net Profit: ₹{profit_data.get('profit', 0)}
            - Predicted 30-Day Growth: {growth_data.get('predicted_growth', 0)}% (Trend: {growth_data.get('trend', 'stable')})
            - Trending Cakes: {trending_data}
            
            Rules:
            1. Return ONLY valid JSON in the exact format specified below. Do not include markdown blocks like ```json ... ```. 
            2. The JSON must be an array of objects.
            3. Each object should have keys: "type", "message", and "priority".
            4. "type" can be: "revenue", "profit", "growth", or "trending" (DO NOT use "stock").
            5. "message" should explicitly reference the numbers provided but interpret them smartly (e.g., "Your ₹X profit means you are retaining Y% margin, which is solid!"). Provide a short, forward-looking prediction in one of the messages based on the predicted growth.
            6. "priority" can be: "success" (positive), "warning" (negative/needs attention), or "info" (neutral).
            
            Example Format:
            [
                {{"type": "revenue", "message": "...", "priority": "success"}},
                {{"type": "profit", "message": "...", "priority": "info"}}
            ]
            """
            
            response = model.generate_content(prompt)
            # Clean up response if it contains markdown formatting
            text = response.text.strip()
            
            # Use regex to find the JSON array if AI included other text
            import re
            json_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)
            elif text.startswith('```json'):
                text = text[7:].strip('` \n')
            elif text.startswith('```'):
                text = text[3:].strip('` \n')
                
            insights = json.loads(text.strip())
            
            # Ensure proper keys exist
            valid_insights = []
            for item in insights:
                if isinstance(item, dict) and 'type' in item and 'message' in item:
                    # Map invalid types to info logic
                    if item.get('type') == 'stock': 
                        item['type'] = 'growth'
                    if item.get('priority') not in ['success', 'warning', 'info']:
                        item['priority'] = 'info'
                    valid_insights.append(item)
            
            if not valid_insights:
                return get_fallback_insights()
                
            return valid_insights[:4] # Limit to 4 maximum

        except Exception as e:
            err_msg = str(e)
            print(f"Gemini Insight Error: {err_msg}")
            if "429" in err_msg or "quota" in err_msg.lower():
                # Provide a more specific fallback message for quota issues
                fallback = get_fallback_insights()
                fallback.append({
                    'type': 'growth',
                    'message': 'AI Analytics is temporarily limited due to high traffic. Real-time data is still accurate.',
                    'priority': 'info'
                })
                return fallback
            return get_fallback_insights()


class CakeDesigner:
    """AI Cake Designer using Gemini"""
    
    @staticmethod
    def calculate_custom_price(requirements: dict) -> int:
        """
        Dynamically estimate price for a custom cake based on requirements.

        Pricing breakdown (in INR):
        - Base rate: ₹500 per kg
        - Flavor premium: Red Velvet/Black Forest +25%, Chocolate/Strawberry +10%
        - Occasion premium: Wedding +40%, Anniversary +20%, Graduation +10%
        - Custom message: +₹100
        - Extra instructions: +₹50
        """
        import re as _re

        # --- Extract weight from size string e.g. '1kg', '2.5 kg', '3Kg' ---
        size_str = str(requirements.get('size', '1')).lower().strip()
        weight_match = _re.search(r'([\d.]+)', size_str)
        weight = float(weight_match.group(1)) if weight_match else 1.0
        # Clamp weight to a sensible range (0.5 – 10 kg)
        weight = max(0.5, min(weight, 10.0))

        base_rate = 500  # INR per kg
        price = base_rate * weight

        # Flavor premium
        flavor = str(requirements.get('flavor', '')).lower()
        if flavor in ('red velvet', 'red_velvet', 'black forest', 'black_forest'):
            price *= 1.25
        elif flavor in ('chocolate', 'strawberry'):
            price *= 1.10
        elif flavor in ('butterscotch', 'mango'):
            price *= 1.05

        # Occasion premium
        occasion = str(requirements.get('occasion', '')).lower()
        if occasion == 'wedding':
            price *= 1.40
        elif occasion == 'anniversary':
            price *= 1.20
        elif occasion == 'graduation':
            price *= 1.10
        elif occasion == 'custom':
            price *= 1.15

        # Message on cake
        if requirements.get('message_on_cake', '').strip():
            price += 100

        # Extra instructions add a small premium
        if requirements.get('extra_instructions', '').strip():
            price += 50

        # Round to nearest 50
        price = int(round(price / 50.0) * 50)
        return max(price, 300)  # Minimum ₹300

    @staticmethod
    def generate_custom_design(requirements):
        """Generate cake design based on requirements using direct Leonardo.ai prompts"""
        from django.conf import settings
        import urllib.parse
        import random
        import re
        import time
        import requests

        def scrub_brands(text):
            """Genericizes known brand names to avoid moderation filters"""
            brands = [
                'batman', 'superman', 'spiderman', 'marvel', 'disney', 'mickey', 
                'minnie', 'star wars', 'jedi', 'pokemon', 'pikachu', 'barbie', 
                'frozen', 'elsa', 'olaf', 'netflix', 'google', 'apple', 'starbucks', 
                'nike', 'adidas', 'pubg', 'fortnite'
            ]
            scrubbed = text
            for brand in brands:
                # Case-insensitive replacement with generic terms
                generic = "superhero" if brand in ['batman', 'superman', 'spiderman', 'marvel'] else "popular character"
                scrubbed = re.sub(rf'\b{brand}\b', f"{generic} themed", scrubbed, flags=re.IGNORECASE)
            return scrubbed

        # 1. GEMINI REQUIREMENT INTERPRETATION (Enriching prompts for Leonardo)
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            
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

            response = model.generate_content(designer_prompt)
            import json
            import re
            
            text = response.text.strip()
            # Extract JSON from potential markdown/conversational filler
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                enriched_data = json.loads(json_match.group(0))
                image_prompt = enriched_data.get('image_prompt', '')
                design_instructions = enriched_data.get('design_instructions', '')
                summary = enriched_data.get('summary', '')
            else:
                # Basic parsing if search fails but it looks like JSON
                enriched_data = json.loads(text.strip('`json\n '))
                image_prompt = enriched_data.get('image_prompt', '')
                design_instructions = enriched_data.get('design_instructions', '')
                summary = enriched_data.get('summary', '')

        except Exception as gemini_err:
            print(f"DEBUG: Gemini Designer Error: {gemini_err}")
            # Fallback to direct construction (old logic) if Gemini fails
            flavor = requirements.get('flavor', 'Classic')
            shape = requirements.get('shape', 'Round')
            size = requirements.get('size', '1kg')
            style = requirements.get('design_style', 'Elegant')
            colors = requirements.get('primary_colors', 'pastel')
            extra = requirements.get('extra_instructions', '')
            
            image_prompt = f"A professional high-quality {size} {shape} {flavor} cake, {style} style, {colors} color palette. {extra}".strip()
            design_instructions = f"Prepare a {size} {shape} {flavor} cake. Use {colors} for frosting and decorations following a {style} style. {extra}"
            summary = f"Custom {style} {flavor} Cake"

        image_prompt = scrub_brands(image_prompt)
        summary = scrub_brands(summary)

        # Prepare response data
        data = {
            'image_description': image_prompt,
            'design_instructions': design_instructions,
            'estimated_price': str(CakeDesigner.calculate_custom_price(requirements)),
            'summary': summary
        }

        # 2. IMAGE GENERATION (Leonardo.ai)
        image_urls = []
        try:
            # Truncate prompt for safety
            if len(image_prompt) > 800:
                image_prompt = image_prompt[:800]
            
            enhanced_prompt = f"{image_prompt}, high-end professional cake photography, sharp focus, 8k, realistic frosting textures, cinematic lighting, appetizing"
            print(f"DEBUG: Leonardo Final Prompt: {enhanced_prompt}")

            if settings.LEONARDO_API_KEY:
                # 1. Create Generation Job
                url = "https://cloud.leonardo.ai/api/rest/v1/generations"
                payload = {
                    "prompt": enhanced_prompt,
                    "modelId": "6b645e3a-d64f-4341-a6d8-7a3690fbf042", # Phoenix
                    "width": 1024,
                    "height": 768,
                    "num_images": 4, 
                    "alchemy": True,
                    "presetStyle": "PHOTOGRAPHY",
                    "public": False
                }
                
                headers = {
                    "accept": "application/json",
                    "content-type": "application/json",
                    "authorization": f"Bearer {settings.LEONARDO_API_KEY}"
                }
                
                print(f"DEBUG: Sending POST to Leonardo (4 images)...")
                response = requests.post(url, json=payload, headers=headers, timeout=20)
                
                if response.status_code == 200:
                    job_data = response.json()
                    if 'sdGenerationJob' in job_data:
                        generation_id = job_data['sdGenerationJob']['generationId']
                        print(f"DEBUG: Leonardo Job SUCCESS: {generation_id}")
                        
                        # 2. Poll for Completion
                        wait_time = 0
                        max_wait = 70 
                        while wait_time < max_wait:
                            time.sleep(5) 
                            wait_time += 5
                            status_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
                            status_response = requests.get(status_url, headers=headers, timeout=10)
                            
                            if status_response.status_code == 200:
                                gen_info = status_response.json()
                                if 'generations_by_pk' in gen_info:
                                    status = gen_info['generations_by_pk']['status']
                                    print(f"DEBUG: Polling Leonardo... Status: {status}")
                                    if status == 'COMPLETE':
                                        for img in gen_info['generations_by_pk'].get('generated_images', []):
                                            image_urls.append(img['url'])
                                        break
                                    elif status == 'FAILED':
                                        break
                else:
                    print(f"DEBUG: Leonardo API Error: {response.status_code}")
                    
        except Exception as leo_error:
            print(f"DEBUG: Leonardo Exception Trace: {leo_error}")

        # 3. FALLBACK (Pollinations - Only if Leonardo failed)
        if len(image_urls) < 4:
            print(f"DEBUG: Filling {4-len(image_urls)} slots with Pollinations...")
            variations = ["soft focus", "studio shot", "side angle", "top view"]
            for i in range(len(image_urls), 4):
                var_prompt = f"{image_prompt}, {variations[i % 4]}"
                encoded_p = urllib.parse.quote(var_prompt)
                seed = random.randint(1, 1000000)
                url = f"https://image.pollinations.ai/prompt/{encoded_p}?width=1024&height=768&seed={seed}&nologo=true&model=flux"
                image_urls.append(url)

        # 4. ROBUST FALLBACK (LoremFlickr)
        fallback_image_urls = []
        for i in range(4):
            f_seed = random.randint(1, 20000)
            fallback_image_urls.append(f"https://loremflickr.com/1024/768/cake,bakery?lock={f_seed}")
        
        data['image_url'] = image_urls[0] if image_urls else fallback_image_urls[0]
        data['image_urls'] = image_urls if image_urls else fallback_image_urls
        data['fallback_image_urls'] = fallback_image_urls
        data['requirements'] = requirements
        
        return data

    @staticmethod
    def _get_simulation_fallback(requirements):
        """Standard simulation fallback for Designer"""
        import urllib.parse
        import random
        
        # Primary: Pollinations
        image_prompt = f"A high quality realistic photo of a {requirements.get('size')} {requirements.get('shape')} cake, {requirements.get('primary_colors')} color theme, {requirements.get('design_style')} style, for {requirements.get('occasion')}, professional food photography, 8k"
        
        if len(image_prompt) > 800:
            image_prompt = image_prompt[:800]
            
        encoded_prompt = urllib.parse.quote(image_prompt)
        
        image_urls = []
        fallback_image_urls = []
        keywords = f"{requirements.get('flavor')},cake"
        
        variations = [
            "cinematic lighting",
            "top view",
            "macro detail",
            "soft focus"
        ]
        
        for i in range(4):
            variation = variations[i]
            seed = random.randint(1, 1000000)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}, {variation}?width=800&height=600&seed={seed}&nologo=true"
            image_urls.append(url)
            
            fallback_seed = random.randint(1, 10000)
            fallback_url = f"https://loremflickr.com/800/600/{keywords}?lock={fallback_seed}"
            fallback_image_urls.append(fallback_url)
        
        return {
            'image_description': f"A beautiful {requirements.get('size')} {requirements.get('shape')} cake in {requirements.get('primary_colors')}. It features a {requirements.get('design_style')} design suitable for a {requirements.get('occasion')}. The frosting is smooth and elegant.",
            'design_instructions': "1. Bake the cake layers as specified.\n2. Apply a crumb coat and chill.\n3. Frost with the primary color buttercream.\n4. Add decorations according to the style.\n5. Pipe the message neatly on top.",
            'estimated_price': str(CakeDesigner.calculate_custom_price(requirements)),
            'summary': f"Custom {requirements.get('flavor')} cake for {requirements.get('occasion')}",
            'image_url': image_urls[0],
            'image_urls': image_urls,
            'fallback_image_url': fallback_image_urls[0],
            'fallback_image_urls': fallback_image_urls
        }

class OCRUtility:
    """OCR Utilities using Gemini AI"""
    
    @staticmethod
    def extract_fssai_number(image_file, target_number=None):
        """
        Extract Enrollment or License Number from image.
        Returns a dict: {'success': bool, 'code': str, 'raw_text': str, 'error': str}
        """
        import google.generativeai as genai
        from django.conf import settings
        import PIL.Image
        import re
        
        if not settings.GEMINI_API_KEY:
            return {'success': False, 'error': 'GEMINI_API_KEY not found in settings'}
            
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            ocr_system_instruction = """
            Extract the FSSAI License Number or Registration Number from this certificate.
            - We are looking for: a 9-character code (6 letters + 3 numbers) or a 14-digit standard number.
            - Return JUST the code with no other text.
            """
            
            model = genai.GenerativeModel(
                model_name='models/gemini-2.5-flash',
                system_instruction=ocr_system_instruction
            )
            
            # Re-open or reset image if needed
            image_file.seek(0)
            img = PIL.Image.open(image_file)
            
            response = model.generate_content(img)
            
            if not response.candidates or not response.candidates[0].content.parts:
                return {'success': False, 'error': 'AI returned empty or blocked response'}
                
            raw_text = response.text.strip().upper()
            result_dict = {'success': False, 'raw_text': raw_text}
            
            # Helper to clean text to just alphanumeric
            def clean_text(t):
                return re.sub(r'[^A-Z0-9]', '', t.upper())

            # 1. Direct Target Match (Cleaned)
            if target_number:
                clean_target = clean_text(target_number)
                clean_raw = clean_text(raw_text)
                
                # Check for direct inclusion
                if clean_target in clean_raw:
                    result_dict['success'] = True
                    result_dict['code'] = target_number.upper()
                    return result_dict
                
                # Fuzzy check: Try common substitutions (O->0, I->1, S->5, etc.)
                def fuzzy_match(target, raw):
                    # Simple common OCR substitutions
                    subs = [('O', '0'), ('I', '1'), ('L', '1'), ('S', '5'), ('B', '8'), ('G', '6'), ('Z', '2')]
                    
                    t_alt = target
                    r_alt = raw
                    for a, b in subs:
                        t_alt = t_alt.replace(a, b)
                        r_alt = r_alt.replace(a, b)
                    
                    return t_alt in r_alt
                
                if fuzzy_match(clean_target, clean_raw):
                    result_dict['success'] = True
                    result_dict['code'] = target_number.upper()
                    return result_dict

            # 2. Extract standard patterns from cleaned text
            packed = clean_text(raw_text)
            
            # Look for specific 9-char patterns
            pattern_6a3n = re.search(r'[A-Z]{6}\d{3}', packed)
            if pattern_6a3n:
                result_dict['success'] = True
                result_dict['code'] = pattern_6a3n.group(0)
                return result_dict

            pattern_6n3a = re.search(r'\d{6}[A-Z]{3}', packed)
            if pattern_6n3a:
                result_dict['success'] = True
                result_dict['code'] = pattern_6n3a.group(0)
                return result_dict
            
            # Look for 14 digits
            digits_14 = re.findall(r'\d{14}', packed)
            if digits_14:
                result_dict['success'] = True
                result_dict['code'] = digits_14[0]
                return result_dict
                
            # Look for any 9 char alphanumeric fallback
            pattern_9char = re.search(r'[A-Z0-9]{9}', packed)
            if pattern_9char:
                result_dict['success'] = True
                result_dict['code'] = pattern_9char.group(0)
                return result_dict

            # General fallback (8-15 chars)
            codes = re.findall(r'[A-Z0-9]{8,15}', packed)
            if codes:
                result_dict['success'] = True
                result_dict['code'] = codes[0]
                return result_dict

            result_dict['error'] = 'Could not find matching pattern in raw text'
            return result_dict
            
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "quota" in err_msg.lower():
                return {'success': False, 'error': 'AI Service busy (Rate Limit). Please try again in 1 minute.'}
            return {'success': False, 'error': f"AI Error: {err_msg}"}
