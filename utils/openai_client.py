from openai import AsyncOpenAI
import json
from config import OPENAI_API_KEY

async def get_ai_chat_response(user_message, pet_info, health_history, is_premium=False, conversation_context=""):
    """🤖 Conversational AI Chat - Natural & Human-like"""
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Detect if this is a greeting or first message
        greetings = ["سلام", "hi", "hello", "درود", "صبح بخیر", "عصر بخیر", "شب بخیر"]
        is_greeting = any(greeting in user_message.lower() for greeting in greetings)
        
        if is_greeting and not conversation_context:
            # First interaction - friendly greeting
            if pet_info and pet_info.get('name'):
                return f"سلام! 😊\n\nمن دامپزشک هوشمند شما هستم. درباره {pet_info['name']} چه سوالی دارید؟\n\n💬 می‌تونید از من بپرسید:\n• مشکلات سلامتی\n• تغذیه و رژیم غذایی\n• رفتار و آموزش\n• مراقبت‌های روزانه\n\n📸 عکس هم می‌تونید بفرستید!"
            else:
                return "سلام! 😊\n\nمن دامپزشک هوشمند شما هستم. چطور می‌تونم کمکتون کنم؟\n\n💬 از من بپرسید:\n• سوالات سلامتی حیوان خانگی\n• مشاوره تغذیه\n• مشکلات رفتاری\n• مراقبت‌های روزانه\n\n📸 عکس هم می‌تونید بفرستید!"
        
        # Create conversational system prompt
        system_prompt = """You are a friendly veterinarian chatbot speaking Persian. 

IMPORTANT RULES:
- Answer ONLY what the user asks
- Don't make assumptions about pets or situations
- Keep responses SHORT (1-3 sentences)
- Be natural and conversational
- Don't mention pet names unless the user mentions them first
- Ask simple follow-up questions

CONVERSATION STYLE:
- Respond directly to what user says
- Use casual, friendly Persian
- Ask "چطور می‌تونم کمکت کنم؟" if unclear
- Don't be overly enthusiastic
- Be helpful but normal

EXAMPLES:
User: "سلام" → "سلام! چطور می‌تونم کمکت کنم؟ 😊"
User: "گربه‌م مریضه" → "چه علامتی دیدی؟ چند وقته این حالت رو داره؟"
User: "چند سالشه؟" → "کدوم حیوان؟ اگر بگی چه نوع حیوانیه بهتر می‌تونم کمک کنم."

Keep it simple and natural!"""
        
        # Format pet context with full details
        pet_context = ""
        if pet_info:
            pet_name = pet_info.get('name', 'حیوان خانگی شما')
            pet_species = pet_info.get('species', '')
            pet_age_years = pet_info.get('age_years', 0)
            pet_age_months = pet_info.get('age_months', 0)
            pet_breed = pet_info.get('breed', '')
            pet_weight = pet_info.get('weight', '')
            pet_gender = pet_info.get('gender', '')
            
            pet_context = f"""
اطلاعات {pet_name}:
- نوع: {pet_species}
- نژاد: {pet_breed if pet_breed else 'نامشخص'}
- سن: {pet_age_years} سال و {pet_age_months} ماه
- وزن: {pet_weight} کیلوگرم
- جنسیت: {pet_gender}
"""
        
        # Format health history if available
        health_context = ""
        if health_history:
            health_context = f"""
تاریخچه سلامت اخیر:
{json.dumps(health_history[-5:], ensure_ascii=False, indent=2)}
"""
        
        user_prompt = f"""
مکالمه قبلی:
{conversation_context}

پیام جدید کاربر: {user_message}
{pet_context}
{health_context}

پاسخ کوتاه، دوستانه و طبیعی بده. به مکالمه قبلی توجه کن. اگر کاربر درباره تاریخچه سلامت پرسید، از اطلاعات موجود استفاده کن.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200,  # Much shorter responses
            temperature=0.8  # More natural/varied
        )
        
        ai_response = response.choices[0].message.content
        
        return ai_response
        
    except Exception as e:
        error_msg = f"❌ خطا در سیستم هوش مصنوعی: {str(e)}"
        print(f"AI Chat Error: {e}")  # For debugging
        return f"{error_msg}\n\n💡 لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."

async def analyze_health(health_data, pet_info, use_reasoning=False):
    """Health Analysis for health tracking feature"""
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Create comprehensive system prompt
        system_prompt = """You are a professional veterinarian providing health analysis in Persian.
        
        IMPORTANT: Start your analysis with a health score in this EXACT format:
        "1. ارزیابی کلی سلامت (امتیاز 0-100): [EMOJI] [SCORE]/100"
        
        Use these emojis based on score:
        - 80-100: 🟢 (green)
        - 60-79: 🟡 (yellow) 
        - 40-59: 🟠 (orange)
        - 0-39: 🔴 (red)
        
        Then provide comprehensive insights including:
        - Trend analysis over time
        - Pattern identification
        - Risk factor assessment
        - Specific recommendations
        - Follow-up plan
        - Important warnings
        
        Respond in Persian with clear, actionable advice."""
        
        # Handle both tuple and dict formats for pet_info
        if isinstance(pet_info, (list, tuple)):
            pet_info_text = f"""
نام: {pet_info[2] if len(pet_info) > 2 else 'نامشخص'}
نوع: {pet_info[3] if len(pet_info) > 3 else 'نامشخص'}
نژاد: {pet_info[4] if len(pet_info) > 4 and pet_info[4] else 'نامشخص'}
سن: {pet_info[5] if len(pet_info) > 5 else 0} سال و {pet_info[6] if len(pet_info) > 6 else 0} ماه
وزن: {pet_info[7] if len(pet_info) > 7 and pet_info[7] else 'نامشخص'} کیلوگرم
جنسیت: {pet_info[8] if len(pet_info) > 8 else 'نامشخص'}
بیماری‌ها: {pet_info[10] if len(pet_info) > 10 and pet_info[10] else 'ندارد'}
داروها: {pet_info[11] if len(pet_info) > 11 and pet_info[11] else 'ندارد'}
            """
        else:
            pet_info_text = json.dumps(pet_info, ensure_ascii=False)
        
        # Handle health_data format
        if isinstance(health_data, str):
            health_data_text = health_data
        else:
            health_data_text = json.dumps(health_data, ensure_ascii=False)
        
        user_prompt = f"""
تحلیل کامل سلامت حیوان خانگی:

اطلاعات حیوان:
{pet_info_text}

داده‌های سلامت:
{health_data_text}

لطفاً تحلیل کاملی از وضعیت سلامت ارائه دهید.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.4
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_msg = f"❌ خطا در سیستم هوش مصنوعی: {str(e)}"
        print(f"AI Error: {e}")  # For debugging
        return f"{error_msg}\n\n💡 لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."

async def generate_diet_plan(pet_details, diet_type, goal, allergies, budget, preference, health_logs):
    """Generate comprehensive diet plan using AI"""
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Create comprehensive system prompt for diet planning
        system_prompt = """You are a professional veterinary nutritionist creating detailed diet plans in Persian.
        
        Create comprehensive, personalized diet plans that include:
        - Daily feeding schedule with exact portions
        - Specific food recommendations with brands if possible
        - Nutritional breakdown (protein, fat, carbs, calories)
        - Weekly meal planning
        - Transition guidelines
        - Monitoring recommendations
        - Budget-appropriate options
        
        Always consider the pet's complete health profile, allergies, and specific goals.
        Provide practical, actionable advice that owners can easily follow."""
        
        # Format pet information
        pet_info_text = f"""
نام: {pet_details['name']}
نوع: {pet_details['species']}
نژاد: {pet_details['breed']}
سن: {pet_details['age_years']} سال و {pet_details['age_months']} ماه
وزن: {pet_details['weight']} کیلوگرم
جنسیت: {pet_details['gender']}
بیماری‌ها: {pet_details['diseases']}
داروها: {pet_details['medications']}
        """
        
        # Format health logs
        health_info = "تاریخچه سلامت موجود نیست"
        if health_logs:
            health_info = "آخرین وضعیت سلامت:\n"
            for log in health_logs[-3:]:  # Last 3 logs
                health_info += f"• {log.get('date', 'نامشخص')}: {log.get('notes', 'بدون یادداشت')}\n"
        
        user_prompt = f"""
🍽️ **درخواست تولید برنامه غذایی**

**اطلاعات حیوان خانگی:**
{pet_info_text}

**مشخصات برنامه غذایی:**
• نوع برنامه: {diet_type}
• هدف اصلی: {goal}
• آلرژی‌ها و محدودیت‌ها: {allergies}
• بودجه ماهانه: {budget}
• ترجیح نوع غذا: {preference}

**وضعیت سلامت:**
{health_info}

لطفاً یک برنامه غذایی کامل و تفصیلی شامل موارد زیر تهیه کنید:

1. **برنامه روزانه غذایی** (صبح، ظهر، عصر، شب)
2. **مقادیر دقیق** (گرم یا فنجان)
3. **پیشنهاد برندهای غذا** (متناسب با بودجه)
4. **جدول هفتگی** (7 روز)
5. **راهنمای انتقال** (تغییر تدریجی رژیم)
6. **نکات مراقبتی** و علائم قابل پیگیری
7. **مکمل‌های پیشنهادی** (در صورت نیاز)

⚠️ **نکات مهم:**
- تمام توصیه‌ها باید علمی و عملی باشند
- آلرژی‌ها را کاملاً در نظر بگیرید
- بودجه را رعایت کنید
- برای تغییرات مهم، مشورت با دامپزشک را توصیه کنید

پاسخ را به فارسی و با فرمت زیبا ارائه دهید.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        diet_plan = response.choices[0].message.content
        
        # Add footer with disclaimer
        from datetime import datetime
        diet_plan += f"""

---
🤖 **تولید شده توسط هوش مصنوعی PetMagix**
📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
⚠️ این برنامه جنبه مشاوره‌ای دارد و جایگزین نظر دامپزشک نیست.
        """
        
        return diet_plan
        
    except Exception as e:
        error_msg = f"❌ خطا در تولید برنامه غذایی: {str(e)}"
        print(f"Diet Plan Generation Error: {e}")  # For debugging
        return f"{error_msg}\n\n💡 لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
