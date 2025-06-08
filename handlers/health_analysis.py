from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.database import db
from utils.keyboards import *
from utils.openai_client import analyze_health
from utils.persian_utils import *
from handlers.subscription import check_user_subscription, is_premium_feature_blocked
import config
import json
import hashlib
from datetime import datetime, timedelta

async def start_health_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start direct health analysis - no second menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pets = db.get_user_pets(user_id)
    
    if not pets:
        await query.edit_message_text(
            "❌ شما هنوز حیوان خانگی اضافه نکرده‌اید.\n"
            "ابتدا یک حیوان خانگی اضافه کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🐕 افزودن حیوان خانگی", callback_data="add_pet")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
            ])
        )
        return
    
    # If only one pet, analyze directly
    if len(pets) == 1:
        await analyze_pet_health_direct(update, pets[0][0])
    else:
        # Multiple pets - show selection
        await query.edit_message_text(
            "🔍 **تحلیل سلامت**\n\n"
            "برای کدام حیوان خانگی می‌خواهید تحلیل سلامت انجام دهید؟",
            reply_markup=pets_list_keyboard(pets),
            parse_mode='Markdown'
        )

async def analyze_pet_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pet selection for analysis"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("analyze_health_"):
        pet_id = int(query.data.split("_")[-1])
        await analyze_pet_health_direct(update, pet_id)
    elif query.data.startswith("select_pet_"):
        pet_id = int(query.data.split("_")[-1])
        await analyze_pet_health_direct(update, pet_id)

async def analyze_pet_health_direct(update, pet_id):
    """Perform direct health analysis based on subscription"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check subscription status
    subscription = check_user_subscription(user_id)
    is_premium = subscription['is_premium']
    
    # Get pet info
    pets = db.get_user_pets(user_id)
    selected_pet = next((pet for pet in pets if pet[0] == pet_id), None)
    
    if not selected_pet:
        await query.edit_message_text(
            "❌ حیوان خانگی یافت نشد.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Get health logs
    health_logs = db.get_pet_health_logs(pet_id, 10)
    
    if not health_logs:
        await query.edit_message_text(
            f"❌ برای {selected_pet[2]} هنوز اطلاعات سلامت ثبت نشده است.\n\n"
            "ابتدا چند روز سلامت حیوان خانگی را ثبت کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 ثبت سلامت", callback_data="health_log")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
            ])
        )
        return
    
    # Show analysis based on subscription
    if is_premium:
        await show_premium_analysis(query, pet_id, selected_pet, health_logs)
    else:
        await show_free_analysis(query, pet_id, selected_pet, health_logs)

async def show_free_analysis(query, pet_id, selected_pet, health_logs):
    """Show simple analysis for free users"""
    await query.edit_message_text(
        f"📊 **تحلیل ساده سلامت {selected_pet[2]}**\n\n"
        "🔍 در حال محاسبه...",
        reply_markup=back_keyboard("back_main"),
        parse_mode='Markdown'
    )
    
    try:
        # Simple health score calculation
        health_score, alerts = calculate_simple_health_score(health_logs)
        latest_log = health_logs[0]
        
        # Create simple analysis
        analysis_text = f"""📊 **تحلیل ساده سلامت {selected_pet[2]}**

🎯 **نمره سلامت**: {english_to_persian_numbers(str(health_score))}/۱۰۰
{get_health_emoji(health_score)} **وضعیت**: {get_health_text(health_score)}

📋 **آخرین وضعیت**:
• وزن: {format_weight(latest_log[3]) if latest_log[3] else 'ثبت نشد'}
• حالت: {latest_log[5] or 'نامشخص'}
• مدفوع: {latest_log[6] or 'نامشخص'}
• فعالیت: {latest_log[9] or 'نامشخص'}

⚠️ **هشدارها**:
{chr(10).join(f'• {alert}' for alert in alerts[:2]) if alerts else '• هیچ هشدار خاصی نیست'}

💡 **توصیه کلی**:
• ادامه ثبت روزانه سلامت
• مراقبت‌های معمول
• در صورت تغییر ناگهانی، مراجعه به دامپزشک

🔒 **برای تحلیل‌های پیشرفته‌تر:**
• تحلیل روندهای هفتگی
• پیش‌بینی مشکلات
• توصیه‌های تخصصی
• گزارش‌های قابل چاپ

**به پریمیوم ارتقاء دهید!**
        """
        
        keyboard = [
            [InlineKeyboardButton("🚀 ارتقاء به پریمیوم", callback_data="upgrade_premium")],
            [InlineKeyboardButton("📊 ثبت سلامت جدید", callback_data="health_log")],
            [InlineKeyboardButton("💬 مشاوره AI", callback_data="ai_chat")],
            [InlineKeyboardButton("🔄 تحلیل مجدد", callback_data=f"analyze_health_{pet_id}")],
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
        ]
        
        await query.edit_message_text(
            analysis_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await query.edit_message_text(
            "❌ خطا در تحلیل سلامت.\n"
            "لطفاً بعداً تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"analyze_health_{pet_id}")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
            ])
        )

async def show_premium_analysis(query, pet_id, selected_pet, health_logs):
    """🧠 Enhanced Premium Analysis with Learning & Multi-Factor Reasoning"""
    user_id = query.from_user.id
    
    await query.edit_message_text(
        f"🧠 **تحلیل هوشمند سلامت {selected_pet[2]}**\n\n"
        "🤖 تحلیل چندعاملی در حال انجام...\n"
        "🔗 بررسی ارتباطات غذا/فعالیت/حالت...\n"
        "📊 شناسایی الگوهای یادگیری...\n"
        "🎯 تشخیص علل ریشه‌ای...\n"
        "📈 پیش‌بینی روندها...\n\n"
        "⏳ لطفاً صبر کنید...",
        reply_markup=back_keyboard("back_main"),
        parse_mode='Markdown'
    )
    
    try:
        print(f"🔍 DEBUG: Starting premium analysis for pet_id={pet_id}, user_id={user_id}")
        
        # 🧠 Enhanced Multi-Factor Analysis
        print("🔍 DEBUG: Getting correlation data...")
        try:
            correlation_data = db.get_correlation_data(pet_id, 30)
            print(f"🔍 DEBUG: Correlation data retrieved: {len(correlation_data) if correlation_data else 0} records")
        except Exception as e:
            print(f"❌ DEBUG: Error getting correlation data: {e}")
            correlation_data = []
        
        print("🔍 DEBUG: Getting learning patterns...")
        try:
            learning_patterns = db.get_ai_learning_patterns(pet_id)
            print(f"🔍 DEBUG: Learning patterns retrieved: {len(learning_patterns) if learning_patterns else 0} patterns")
        except Exception as e:
            print(f"❌ DEBUG: Error getting learning patterns: {e}")
            learning_patterns = []
        
        print("🔍 DEBUG: Getting historical patterns...")
        try:
            historical_patterns = db.get_pet_historical_patterns(pet_id)
            print(f"🔍 DEBUG: Historical patterns retrieved: {len(historical_patterns) if historical_patterns else 0} patterns")
        except Exception as e:
            print(f"❌ DEBUG: Error getting historical patterns: {e}")
            historical_patterns = []
        
        # Analyze correlations between diet/activity/mood
        print("🔍 DEBUG: Analyzing correlations...")
        try:
            correlations = analyze_diet_activity_correlations(correlation_data)
            print(f"🔍 DEBUG: Correlations analyzed successfully")
        except Exception as e:
            print(f"❌ DEBUG: Error analyzing correlations: {e}")
            correlations = {"diet_mood_links": [], "activity_symptoms_links": [], "food_intake_patterns": [], "detected_triggers": []}
        
        # Multi-factor reasoning analysis
        print("🔍 DEBUG: Calculating enhanced health score...")
        try:
            health_score, alerts, trends, root_causes = calculate_enhanced_health_score(
                health_logs, selected_pet, correlations, learning_patterns
            )
            print(f"🔍 DEBUG: Health score calculated: {health_score}")
        except Exception as e:
            print(f"❌ DEBUG: Error calculating health score: {e}")
            health_score, alerts, trends, root_causes = 75, ["خطا در محاسبه"], "خطا در تحلیل روند", []
        
        # Convert selected_pet tuple to dictionary for AI analysis
        print("🔍 DEBUG: Converting pet data to dictionary...")
        try:
            pet_dict = {
                "id": selected_pet[0],
                "user_id": selected_pet[1],
                "name": selected_pet[2],
                "species": selected_pet[3],
                "breed": selected_pet[4] if selected_pet[4] else "نامشخص",
                "age_years": selected_pet[5] if selected_pet[5] else 0,
                "age_months": selected_pet[6] if selected_pet[6] else 0,
                "weight": selected_pet[7] if selected_pet[7] else 0,
                "gender": selected_pet[8] if selected_pet[8] else "نامشخص",
                "is_neutered": selected_pet[9] if len(selected_pet) > 9 else False,
                "diseases": selected_pet[10] if len(selected_pet) > 10 and selected_pet[10] else "ندارد",
                "medications": selected_pet[11] if len(selected_pet) > 11 and selected_pet[11] else "ندارد",
                "vaccine_status": selected_pet[12] if len(selected_pet) > 12 and selected_pet[12] else "نامشخص"
            }
            print(f"🔍 DEBUG: Pet dictionary created successfully")
        except Exception as e:
            print(f"❌ DEBUG: Error creating pet dictionary: {e}")
            pet_dict = {"name": "نامشخص", "species": "نامشخص", "breed": "نامشخص"}
        
        # Check for uploaded images in latest health logs
        print("🔍 DEBUG: Checking for uploaded images...")
        image_analysis_context = ""
        try:
            from utils.openai_client import extract_image_insights_for_health_analysis
            # Pass both health_logs and pet_dict as required arguments
            image_insights = await extract_image_insights_for_health_analysis(health_logs[:3], pet_dict)
            
            if image_insights and "امکان تحلیل تصویر موجود نیست" not in image_insights:
                print(f"🔍 DEBUG: Image analysis completed successfully")
                image_analysis_context = f"\n\n📸 **تحلیل تصاویر آپلود شده:**\n{image_insights}\n"
            else:
                print("🔍 DEBUG: No images found in recent health logs or analysis failed")
        except Exception as e:
            print(f"❌ DEBUG: Error analyzing images: {e}")
            image_analysis_context = "\n\n⚠️ تصویر آپلود شده قابل تحلیل نبود یا نامشخص بود"

        # Enhanced AI analysis with learning context and image insights
        print("🔍 DEBUG: Getting AI analysis...")
        try:
            ai_analysis = await get_enhanced_ai_analysis(
                pet_dict, health_logs, correlations, learning_patterns, user_id, image_analysis_context
            )
            print(f"🔍 DEBUG: AI analysis completed: {len(ai_analysis) if ai_analysis else 0} characters")
        except Exception as e:
            print(f"❌ DEBUG: Error in AI analysis: {e}")
            ai_analysis = f"❌ خطا در تحلیل هوش مصنوعی: {str(e)[:100]}..."
        
        # Generate consultation ID for feedback
        print("🔍 DEBUG: Generating consultation ID...")
        try:
            consultation_id = generate_consultation_id(user_id, pet_id, "health_analysis")
            print(f"🔍 DEBUG: Consultation ID generated: {consultation_id}")
        except Exception as e:
            print(f"❌ DEBUG: Error generating consultation ID: {e}")
            consultation_id = "error_id"
        
        # Store analysis for learning
        print("🔍 DEBUG: Storing analysis for learning...")
        try:
            await store_analysis_for_learning(pet_id, ai_analysis, correlations, consultation_id)
            print("🔍 DEBUG: Analysis stored successfully")
        except Exception as e:
            print(f"❌ DEBUG: Error storing analysis: {e}")
        
        # Create enhanced analysis text
        print("🔍 DEBUG: Creating analysis text...")
        try:
            analysis_text = f"""🧠 **تحلیل هوشمند سلامت {selected_pet[2]}**

🤖 **تحلیل هوش مصنوعی با یادگیری**:
{ai_analysis}

🔗 **ارتباطات شناسایی شده**:
{format_correlations(correlations)}

🎯 **علل ریشه‌ای احتمالی**:
{format_root_causes(root_causes)}

📈 **تحلیل روندها**:
{trends}

⚠️ **هشدارهای هوشمند**:
{chr(10).join(f'• {alert}' for alert in alerts[:3]) if alerts else '• هیچ هشدار خاصی نیست'}

💡 **توصیه‌های تخصصی**:
{generate_smart_recommendations(correlations, root_causes)}

📊 **آمار**: {english_to_persian_numbers(str(len(health_logs)))} ثبت | 🧠 {len(learning_patterns)} الگو یادگیری
            """
            print("🔍 DEBUG: Analysis text created successfully")
        except Exception as e:
            print(f"❌ DEBUG: Error creating analysis text: {e}")
            analysis_text = f"❌ خطا در تولید متن تحلیل: {str(e)}"
        
        # Add feedback buttons for AI quality assessment
        print("🔍 DEBUG: Creating feedback keyboard...")
        try:
            feedback_keyboard = create_feedback_keyboard(consultation_id, pet_id)
            print("🔍 DEBUG: Feedback keyboard created successfully")
        except Exception as e:
            print(f"❌ DEBUG: Error creating feedback keyboard: {e}")
            feedback_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
            ])
        
        print("🔍 DEBUG: Sending final analysis message...")
        await query.edit_message_text(
            analysis_text,
            reply_markup=feedback_keyboard,
            parse_mode='Markdown'
        )
        print("🔍 DEBUG: Premium analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ DEBUG: CRITICAL ERROR in show_premium_analysis: {e}")
        print(f"❌ DEBUG: Error type: {type(e).__name__}")
        print(f"❌ DEBUG: Error args: {e.args}")
        
        import traceback
        print(f"❌ DEBUG: Full traceback:")
        traceback.print_exc()
        
        await query.edit_message_text(
            f"❌ خطا در تحلیل سلامت.\n"
            f"جزئیات خطا: {str(e)[:200]}...\n\n"
            "لطفاً بعداً تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"analyze_health_{pet_id}")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
            ])
        )

def calculate_simple_health_score(health_logs):
    """Calculate simple health score for free users"""
    if not health_logs:
        return 50, []
    
    score = 100
    alerts = []
    latest_log = health_logs[0]
    
    # Simple checks
    if latest_log[6] == "خونی":  # Blood in stool
        score -= 30
        alerts.append("🔴 خون در مدفوع - مراجعه فوری")
    
    if latest_log[5] == "خسته و بی‌حال":  # Tired
        score -= 15
        alerts.append("🟠 حالت خستگی")
    
    if latest_log[9] == "کم":  # Low activity
        score -= 10
        alerts.append("🟡 فعالیت پایین")
    
    # Weight check if multiple logs
    if len(health_logs) >= 2:
        weights = [log[3] for log in health_logs[:2] if log[3]]
        if len(weights) == 2 and weights[1] > 0:
            weight_change = abs(weights[0] - weights[1]) / weights[1] * 100
            if weight_change > 10:
                score -= 20
                alerts.append("🔴 تغییر وزن زیاد")
    
    score = max(0, min(100, score))
    return score, alerts

def calculate_advanced_health_score(health_logs, pet_info):
    """Calculate advanced health score with trends"""
    if not health_logs:
        return 50, [], "داده کافی نیست"
    
    score = 100
    alerts = []
    
    recent_logs = health_logs[:5]
    latest_log = health_logs[0]
    
    # Weight analysis
    weights = [log[3] for log in recent_logs if log[3]]
    if len(weights) >= 2:
        weight_change = abs(weights[0] - weights[1]) / weights[1] * 100 if weights[1] > 0 else 0
        if weight_change > 5:
            score -= 20
            alerts.append("🔴 تغییر ناگهانی وزن")
        elif weight_change > 2:
            score -= 10
            alerts.append("🟠 تغییر وزن قابل توجه")
    
    # Mood analysis
    moods = [log[5] for log in recent_logs if log[5]]
    bad_moods = sum(1 for mood in moods if mood in ["خسته و بی‌حال", "اضطراب"])
    if bad_moods >= 2:
        score -= 15
        alerts.append("🔴 حالت روحی نامناسب")
    elif bad_moods == 1:
        score -= 8
        alerts.append("🟠 نگرانی حالت روحی")
    
    # Stool analysis
    stools = [log[6] for log in recent_logs if log[6]]
    bloody_stools = sum(1 for stool in stools if stool == "خونی")
    if bloody_stools >= 1:
        score -= 25
        alerts.append("🔴 خون در مدفوع")
    
    # Activity analysis
    activities = [log[9] for log in recent_logs if log[9]]
    low_activities = sum(1 for activity in activities if activity == "کم")
    if low_activities >= 2:
        score -= 10
        alerts.append("🟠 فعالیت پایین مداوم")
    
    score = max(0, min(100, score))
    
    # Generate trends
    trends = generate_trends(health_logs)
    
    return score, alerts, trends

def generate_trends(health_logs):
    """Generate trend analysis"""
    if len(health_logs) < 3:
        return "داده کافی برای تحلیل روند نیست"
    
    trends = []
    
    # Weight trend
    weights = [log[3] for log in health_logs[:5] if log[3]]
    if len(weights) >= 3:
        if weights[0] > weights[-1]:
            trends.append("📉 روند وزن: کاهشی")
        elif weights[0] < weights[-1]:
            trends.append("📈 روند وزن: افزایشی")
        else:
            trends.append("➡️ روند وزن: ثابت")
    
    # Mood trend
    moods = [log[5] for log in health_logs[:5] if log[5]]
    if moods:
        good_moods = sum(1 for mood in moods if mood in ["شاد و پرانرژی", "عادی"])
        mood_percentage = (good_moods / len(moods)) * 100
        
        if mood_percentage >= 80:
            trends.append("😊 روند حالت: مثبت")
        elif mood_percentage >= 60:
            trends.append("😐 روند حالت: متوسط")
        else:
            trends.append("😟 روند حالت: نگران‌کننده")
    
    return "\n".join(trends) if trends else "روندهای خاصی شناسایی نشد"

def format_pet_info(pet_data):
    """Format pet info for AI"""
    return f"""
نام: {pet_data[2]}
نوع: {pet_data[3]}
نژاد: {pet_data[4] or 'نامشخص'}
سن: {format_age(pet_data[5], pet_data[6])}
وزن: {format_weight(pet_data[7])}
جنسیت: {pet_data[8]}
بیماری‌ها: {pet_data[10] or 'ندارد'}
داروها: {pet_data[11] or 'ندارد'}
    """

def format_health_data(health_logs):
    """Format health data for AI"""
    health_data = "آخرین ثبت‌های سلامت:\n"
    for i, log in enumerate(health_logs[:5], 1):
        health_data += f"""
ثبت {i}:
- وزن: {format_weight(log[3]) if log[3] else 'ثبت نشد'}
- حالت: {log[5] or 'نامشخص'}
- مدفوع: {log[6] or 'نامشخص'}
- فعالیت: {log[9] or 'نامشخص'}
        """
    return health_data

def get_health_emoji(score):
    """Get emoji for health score"""
    if score >= 80:
        return "🟢"
    elif score >= 60:
        return "🟡"
    elif score >= 40:
        return "🟠"
    else:
        return "🔴"

def get_health_text(score):
    """Get text for health score"""
    if score >= 80:
        return "سالم"
    elif score >= 60:
        return "نرمال"
    elif score >= 40:
        return "نیازمند پیگیری"
    else:
        return "نگران‌کننده"

async def show_pet_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pet health history"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("history_"):
        pet_id = int(query.data.split("_")[-1])
        user_id = update.effective_user.id
        
        pets = db.get_user_pets(user_id)
        selected_pet = next((pet for pet in pets if pet[0] == pet_id), None)
        
        if not selected_pet:
            await query.edit_message_text(
                "❌ حیوان خانگی یافت نشد.",
                reply_markup=main_menu_keyboard()
            )
            return
        
        health_logs = db.get_pet_health_logs(pet_id, 10)
        
        if not health_logs:
            await query.edit_message_text(
                f"❌ برای {selected_pet[2]} هنوز اطلاعات سلامت ثبت نشده است.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 ثبت سلامت", callback_data="health_log")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=f"select_pet_{pet_id}")]
                ])
            )
            return
        
        history_text = f"📋 **تاریخچه سلامت {selected_pet[2]}**\n\n"
        
        for i, log in enumerate(health_logs, 1):
            history_text += f"""
**ثبت {english_to_persian_numbers(str(i))}:**
⚖️ وزن: {format_weight(log[3]) if log[3] else 'ثبت نشد'}
😊 حالت: {log[5] or 'نامشخص'}
💩 مدفوع: {log[6] or 'نامشخص'}
🏃 فعالیت: {log[9] or 'نامشخص'}
📝 یادداشت: {log[10] or 'ندارد'}
---
            """
        
        await query.edit_message_text(
            history_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📈 تحلیل سلامت", callback_data=f"analyze_health_{pet_id}")],
                [InlineKeyboardButton("📊 ثبت جدید", callback_data="health_log")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data=f"select_pet_{pet_id}")]
            ]),
            parse_mode='Markdown'
        )

# 🧠 Enhanced Premium Functions with Learning & Multi-Factor Reasoning

def analyze_diet_activity_correlations(correlation_data):
    """🔗 Analyze correlations between diet, activity, and mood"""
    correlations = {
        "diet_mood_links": [],
        "activity_symptoms_links": [],
        "food_intake_patterns": [],
        "detected_triggers": []
    }
    
    if len(correlation_data) < 3:
        return correlations
    
    # Analyze with actual database structure: date, food_type, mood, stool_info, symptoms, weight, activity_level, notes
    for i in range(1, len(correlation_data)):
        current = correlation_data[i-1]
        previous = correlation_data[i]
        
        # Diet-Mood correlation (food_type vs mood)
        if current[1] and current[1] != previous[1]:  # food_type changed
            if current[2] != previous[2]:  # mood changed
                correlations["diet_mood_links"].append({
                    "date": current[0],
                    "diet_change": f"تغییر از {previous[1]} به {current[1]}",
                    "mood_before": previous[2],
                    "mood_after": current[2],
                    "correlation_type": "diet_mood"
                })
        
        # Food type vs symptoms
        if current[1] and current[4]:  # food_type and symptoms
            correlations["food_intake_patterns"].append({
                "date": current[0],
                "food_notes": current[1],
                "symptoms": current[4],
                "correlation_type": "food_symptoms"
            })
        
        # Activity vs symptoms
        if current[6] and current[4]:  # activity_level and symptoms
            if current[6] != previous[6]:  # activity changed
                correlations["activity_symptoms_links"].append({
                    "date": current[0],
                    "activity_change": f"تغییر از {previous[6]} به {current[6]}",
                    "symptoms": current[4],
                    "correlation_type": "activity_symptoms"
                })
    
    # Detect recurring triggers
    correlations["detected_triggers"] = detect_health_triggers(correlation_data)
    
    return correlations

def detect_health_triggers(correlation_data):
    """🎯 Detect recurring health triggers"""
    triggers = []
    
    # Look for patterns in food type followed by symptoms
    # Database structure: date, food_type, mood, stool_info, symptoms, weight, activity_level, notes
    food_symptom_pairs = []
    for row in correlation_data:
        if row[1] and row[4]:  # food_type and symptoms
            food_symptom_pairs.append((row[1], row[4]))
    
    # Find recurring patterns
    from collections import Counter
    pattern_counts = Counter(food_symptom_pairs)
    
    for (food_type, symptom), count in pattern_counts.items():
        if count >= 2:  # Recurring pattern
            triggers.append({
                "trigger": food_type,
                "effect": symptom,
                "frequency": count,
                "confidence": min(0.9, count * 0.3)
            })
    
    return triggers

def calculate_enhanced_health_score(health_logs, pet_info, correlations, learning_patterns):
    """🧠 Enhanced health score with multi-factor reasoning"""
    if not health_logs:
        return 50, [], "داده کافی نیست", []
    
    score = 100
    alerts = []
    root_causes = []
    
    recent_logs = health_logs[:7]  # Last week
    
    # Basic health analysis
    score, basic_alerts, trends = calculate_advanced_health_score(health_logs, pet_info)
    alerts.extend(basic_alerts)
    
    # Multi-factor correlation analysis
    if correlations["diet_mood_links"]:
        for link in correlations["diet_mood_links"]:
            if "خسته" in link["mood_after"] and "شاد" in link["mood_before"]:
                score -= 5
                alerts.append(f"🔗 تغییر غذا '{link['diet_change']}' باعث کاهش انرژی شده")
                root_causes.append({
                    "cause": "تغییر رژیم غذایی",
                    "effect": "کاهش انرژی",
                    "evidence": f"تاریخ: {link['date']}"
                })
    
    # Food intake correlation analysis
    if correlations["food_intake_patterns"]:
        for pattern in correlations["food_intake_patterns"]:
            if any(word in pattern["symptoms"].lower() for word in ["اسهال", "استفراغ", "درد"]):
                score -= 8
                alerts.append(f"🍽️ ارتباط بین غذا و علائم: {pattern['food_notes']}")
                root_causes.append({
                    "cause": "نوع غذا",
                    "effect": pattern["symptoms"],
                    "evidence": f"یادداشت: {pattern['food_notes']}"
                })
    
    # Activity correlation analysis
    if correlations["activity_symptoms_links"]:
        for link in correlations["activity_symptoms_links"]:
            if "کم" in link["activity_change"] and link["symptoms"]:
                score -= 6
                alerts.append(f"🏃 کاهش فعالیت مرتبط با: {link['symptoms']}")
                root_causes.append({
                    "cause": "کاهش فعالیت",
                    "effect": link["symptoms"],
                    "evidence": f"تغییر فعالیت: {link['activity_change']}"
                })
    
    # Trigger pattern analysis
    if correlations["detected_triggers"]:
        for trigger in correlations["detected_triggers"]:
            if trigger["confidence"] > 0.6:
                score -= 10
                alerts.append(f"⚠️ محرک شناسایی شده: {trigger['trigger']} → {trigger['effect']}")
                root_causes.append({
                    "cause": trigger["trigger"],
                    "effect": trigger["effect"],
                    "evidence": f"تکرار {trigger['frequency']} بار"
                })
    
    # Learning pattern integration
    for pattern in learning_patterns:
        try:
            pattern_data = json.loads(pattern[3])
            if pattern[4] > 0.7:  # High confidence pattern
                if pattern[2] == "health_decline":
                    score -= 5
                    alerts.append(f"🧠 الگوی یادگیری: {pattern_data.get('description', 'الگوی منفی')}")
        except:
            continue
    
    score = max(0, min(100, score))
    return score, alerts, trends, root_causes

async def get_enhanced_ai_analysis(pet_info, health_logs, correlations, learning_patterns, user_id, image_analysis_context=""):
    """🤖 Enhanced Premium AI Analysis with Complete Pet Data & Image Analysis"""
    try:
        print("🔍 DEBUG: Starting premium analysis for pet_id={}, user_id={}".format(pet_info.get('pet_id'), user_id))
        
        # Get comprehensive pet data
        pet_context = format_comprehensive_pet_info(pet_info)
        health_context = format_comprehensive_health_data(health_logs)
        
        # Add correlation analysis
        correlation_context = ""
        if correlations.get("diet_mood_links"):
            correlation_context += "🔗 **ارتباطات غذا-حالت:**\n"
            for link in correlations["diet_mood_links"][:3]:
                correlation_context += f"- {link.get('diet_change', 'تغییر غذا')} → {link.get('mood_after', 'تغییر حالت')}\n"
        
        if correlations.get("detected_triggers"):
            correlation_context += "\n⚠️ **محرک‌های شناسایی شده:**\n"
            for trigger in correlations["detected_triggers"][:2]:
                correlation_context += f"- {trigger.get('trigger', 'محرک')} → {trigger.get('effect', 'اثر')}\n"
        
        # Add learning patterns
        learning_context = ""
        if learning_patterns:
            learning_context = "🧠 **الگوهای یادگیری قبلی:**\n"
            for pattern in learning_patterns[:3]:
                try:
                    pattern_data = json.loads(pattern[3]) if pattern[3] else {}
                    learning_context += f"- {pattern[2]}: {pattern_data.get('summary', 'الگو شناسایی شده')}\n"
                except:
                    learning_context += f"- {pattern[2] if len(pattern) > 2 else 'الگو'}: داده‌های تحلیلی\n"
        
        # Get historical trends
        historical_trends = analyze_health_trends_comprehensive(health_logs)
        
        # Get breed-specific insights
        if isinstance(pet_info, (list, tuple)):
            breed = pet_info[4] if len(pet_info) > 4 else ''
            species = pet_info[3] if len(pet_info) > 3 else ''
        else:
            breed = pet_info.get('breed', '')
            species = pet_info.get('species', '')
        
        breed_insights = get_breed_specific_insights(breed, species)
        
        # Enhanced AI prompt with comprehensive analysis including image insights
        enhanced_prompt = f"""
🔬 **تحلیل جامع سلامت حیوان خانگی - نسخه پریمیوم**

📋 **اطلاعات کامل حیوان:**
{pet_context}

📊 **تاریخچه سلامت (30 روز اخیر):**
{health_context}

📈 **روندهای تاریخی:**
{historical_trends}

🔗 **تحلیل ارتباطات:**
{correlation_context}

🧠 **الگوهای یادگیری:**
{learning_context}

🧬 **بینش‌های نژادی:**
{breed_insights}

{image_analysis_context}

**درخواست تحلیل:**
لطفاً تحلیل جامع و پیشرفته‌ای از وضعیت سلامت این حیوان ارائه دهید که شامل:

1. **ارزیابی کلی سلامت** (امتیاز 0-100)
2. **تحلیل روندها** (بهبود/بدتر شدن/پایدار)
3. **شناسایی الگوها** (الگوهای رفتاری، غذایی، سلامتی)
4. **پیش‌بینی ریسک‌ها** (ریسک‌های آینده بر اساس داده‌ها)
5. **توصیه‌های تخصصی** (اقدامات پیشگیرانه و درمانی)
6. **برنامه پیگیری** (چه چیزهایی را باید مراقب باشیم)
7. **هشدارهای مهم** (علائمی که نیاز به مراجعه فوری دارند)

**⚠️ مهم:** اگر تصاویر آپلود شده‌ای وجود دارد، حتماً آن‌ها را در تحلیل خود لحاظ کنید:
- اگر آزمایش خون است: مقادیر غیرطبیعی را در هشدارها و علل ریشه‌ای ذکر کنید
- اگر نسخه دامپزشک است: داروها و تشخیص را در توصیه‌ها بگنجانید  
- اگر عکس حیوان است: علائم ظاهری را در ارزیابی کلی در نظر بگیرید

تحلیل باید بر اساس داده‌های واقعی و علمی باشد و شامل:
1. بررسی ارتباط بین تغییرات غذا، فعالیت و حالت
2. شناسایی علل ریشه‌ای احتمالی (شامل یافته‌های تصاویر)
3. توصیه‌های عملی بر اساس الگوهای شناسایی شده
4. پیش‌بینی روند سلامت

تحلیل باید عمیق، دقیق و قابل اجرا باشد.
        """
        
        ai_response = await analyze_health(enhanced_prompt, pet_context, use_reasoning=True)
        
        if ai_response and len(ai_response.strip()) > 50:
            return ai_response
        else:
            return "تحلیل AI با موفقیت انجام نشد - لطفاً دوباره تلاش کنید"
            
    except Exception as e:
        return f"خطا در تحلیل AI: {str(e)[:100]}..."

def format_correlations(correlations):
    """📊 Format correlations for display"""
    if not any(correlations.values()):
        return "• هیچ ارتباط خاصی شناسایی نشد"
    
    formatted = []
    
    if correlations["diet_mood_links"]:
        formatted.append("🍽️ **ارتباط غذا-حالت:**")
        for link in correlations["diet_mood_links"][:2]:
            formatted.append(f"  • {link['diet_change']} → {link['mood_after']}")
    
    if correlations["detected_triggers"]:
        formatted.append("⚠️ **محرک‌های شناسایی شده:**")
        for trigger in correlations["detected_triggers"][:2]:
            formatted.append(f"  • {trigger['trigger']} → {trigger['effect']} ({trigger['frequency']} بار)")
    
    if correlations["activity_symptoms_links"]:
        formatted.append("🏃 **ارتباط فعالیت-علائم:**")
        for link in correlations["activity_symptoms_links"][:2]:
            formatted.append(f"  • {link['activity_change']} → {link['symptoms']}")
    
    return "\n".join(formatted) if formatted else "• ارتباطات در حال بررسی..."

def format_root_causes(root_causes):
    """🎯 Format root causes for display"""
    if not root_causes:
        return "• علل ریشه‌ای خاصی شناسایی نشد"
    
    formatted = []
    for cause in root_causes[:3]:
        formatted.append(f"• **{cause['cause']}** → {cause['effect']}")
        formatted.append(f"  📋 {cause['evidence']}")
    
    return "\n".join(formatted)

def generate_smart_recommendations(correlations, root_causes):
    """💡 Generate smart recommendations based on analysis"""
    recommendations = []
    
    # Diet-based recommendations
    if correlations["diet_mood_links"]:
        recommendations.append("🍽️ **تغذیه:** بازگشت به رژیم قبلی که حالت بهتری داشت")
    
    if correlations["detected_triggers"]:
        for trigger in correlations["detected_triggers"][:1]:
            recommendations.append(f"⚠️ **اجتناب:** از {trigger['trigger']} خودداری کنید")
    
    # Activity-based recommendations
    if correlations["activity_symptoms_links"]:
        recommendations.append("🏃 **فعالیت:** تدریجی افزایش فعالیت و نظارت بر علائم")
    
    # Root cause recommendations
    for cause in root_causes[:2]:
        if "غذا" in cause["cause"]:
            recommendations.append("🔍 **بررسی:** مشورت با دامپزشک درباره رژیم غذایی")
        elif "فعالیت" in cause["cause"]:
            recommendations.append("💪 **تمرین:** برنامه تمرینی تدریجی و کنترل شده")
    
    # Default recommendations
    if not recommendations:
        recommendations = [
            "📊 ادامه ثبت دقیق اطلاعات روزانه",
            "🔄 نظارت بر تغییرات و الگوها",
            "👨‍⚕️ مشورت دوره‌ای با دامپزشک"
        ]
    
    return "\n".join(recommendations[:4])

def generate_consultation_id(user_id, pet_id, analysis_type):
    """🆔 Generate unique consultation ID for feedback"""
    timestamp = str(int(datetime.now().timestamp()))
    data = f"{user_id}_{pet_id}_{analysis_type}_{timestamp}"
    return hashlib.md5(data.encode()).hexdigest()[:12]

async def store_analysis_for_learning(pet_id, ai_analysis, correlations, consultation_id):
    """💾 Store analysis results for AI learning"""
    try:
        # Store learning patterns
        if correlations["detected_triggers"]:
            for trigger in correlations["detected_triggers"]:
                pattern_data = {
                    "trigger": trigger["trigger"],
                    "effect": trigger["effect"],
                    "confidence": trigger["confidence"],
                    "consultation_id": consultation_id
                }
                db.store_ai_learning_pattern(
                    pet_id, 
                    "health_trigger", 
                    json.dumps(pattern_data, ensure_ascii=False),
                    trigger["confidence"]
                )
        
        # Store correlation patterns
        if correlations["diet_mood_links"]:
            pattern_data = {
                "correlations": correlations["diet_mood_links"],
                "analysis_date": datetime.now().isoformat(),
                "consultation_id": consultation_id
            }
            db.store_ai_learning_pattern(
                pet_id,
                "diet_mood_correlation",
                json.dumps(pattern_data, ensure_ascii=False),
                0.8
            )
        
        return True
    except Exception as e:
        print(f"Error storing analysis for learning: {e}")
        return False

def create_feedback_keyboard(consultation_id, pet_id):
    """⭐ Create feedback keyboard for AI quality assessment"""
    keyboard = [
        [
            InlineKeyboardButton("⭐", callback_data=f"feedback_{consultation_id}_1"),
            InlineKeyboardButton("⭐⭐", callback_data=f"feedback_{consultation_id}_2"),
            InlineKeyboardButton("⭐⭐⭐", callback_data=f"feedback_{consultation_id}_3"),
            InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"feedback_{consultation_id}_4"),
            InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"feedback_{consultation_id}_5")
        ],
        [
            InlineKeyboardButton("✅ تحلیل مفید بود", callback_data=f"feedback_useful_{consultation_id}"),
            InlineKeyboardButton("❌ تحلیل اشتباه بود", callback_data=f"feedback_wrong_{consultation_id}")
        ],
        [
            InlineKeyboardButton("📊 ثبت سلامت جدید", callback_data="health_log"),
            InlineKeyboardButton("📋 تاریخچه کامل", callback_data=f"history_{pet_id}")
        ],
        [
            InlineKeyboardButton("💬 مشاوره AI", callback_data="ai_chat"),
            InlineKeyboardButton("🔄 تحلیل مجدد", callback_data=f"analyze_health_{pet_id}")
        ],
        [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
    ]
    
    return InlineKeyboardMarkup(keyboard)

# 📝 Feedback Handler Functions

async def handle_ai_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle AI feedback from users"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data
    
    if callback_data.startswith("feedback_"):
        parts = callback_data.split("_")
        
        if len(parts) >= 3:
            consultation_id = parts[1]
            
            if parts[2].isdigit():  # Star rating
                rating = int(parts[2])
                await process_star_feedback(query, user_id, consultation_id, rating)
            elif parts[2] == "useful":
                await process_useful_feedback(query, user_id, consultation_id, True)
            elif parts[2] == "wrong":
                await process_useful_feedback(query, user_id, consultation_id, False)

async def process_star_feedback(query, user_id, consultation_id, rating):
    """Process star rating feedback"""
    try:
        # Store feedback in database
        db.store_ai_feedback_enhanced(
            user_id=user_id,
            pet_id=0,  # Will be extracted from consultation_id if needed
            consultation_id=consultation_id,
            ai_type="health_analysis",
            rating=rating,
            feedback_type="star_rating"
        )
        
        # Show thank you message
        feedback_text = f"🙏 متشکریم! امتیاز {rating} ستاره ثبت شد.\n\nبازخورد شما به بهبود کیفیت تحلیل کمک می‌کند."
        
        await query.edit_message_text(
            feedback_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به تحلیل", callback_data="health_analysis")],
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_main")]
            ])
        )
        
    except Exception as e:
        await query.edit_message_text(
            "❌ خطا در ثبت بازخورد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="health_analysis")]
            ])
        )

async def process_useful_feedback(query, user_id, consultation_id, is_useful):
    """Process useful/wrong feedback"""
    try:
        feedback_type = "useful" if is_useful else "wrong"
        rating = 5 if is_useful else 1
        
        # Store feedback
        db.store_ai_feedback_enhanced(
            user_id=user_id,
            pet_id=0,
            consultation_id=consultation_id,
            ai_type="health_analysis",
            rating=rating,
            feedback_type=feedback_type
        )
        
        if is_useful:
            feedback_text = "✅ عالی! تحلیل مفید بودن ثبت شد.\n\nما همچنان در حال بهبود سیستم هستیم."
        else:
            feedback_text = "❌ متأسفیم که تحلیل مفید نبود.\n\nبازخورد شما برای بهبود سیستم ثبت شد.\n\n💡 پیشنهاد: با دامپزشک مشورت کنید."
        
        await query.edit_message_text(
            feedback_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 مشاوره AI", callback_data="ai_chat")],
                [InlineKeyboardButton("🔙 بازگشت به تحلیل", callback_data="health_analysis")],
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_main")]
            ])
        )
        
    except Exception as e:
        await query.edit_message_text(
            "❌ خطا در ثبت بازخورد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="health_analysis")]
            ])
        )

# 🔧 Helper Functions for Enhanced Analysis

def format_comprehensive_pet_info(pet_data):
    """📋 Format comprehensive pet information"""
    if isinstance(pet_data, (list, tuple)):
        # Handle tuple/list format from database
        return f"""
نام: {pet_data[2] if len(pet_data) > 2 else 'نامشخص'}
نوع: {pet_data[3] if len(pet_data) > 3 else 'نامشخص'}
نژاد: {pet_data[4] if len(pet_data) > 4 and pet_data[4] else 'نامشخص'}
سن: {format_age(pet_data[5] if len(pet_data) > 5 else 0, pet_data[6] if len(pet_data) > 6 else 0)}
وزن: {format_weight(pet_data[7]) if len(pet_data) > 7 and pet_data[7] else 'نامشخص'}
جنسیت: {pet_data[8] if len(pet_data) > 8 else 'نامشخص'}
عقیم شده: {'بله' if len(pet_data) > 9 and pet_data[9] else 'خیر'}
بیماری‌ها: {pet_data[10] if len(pet_data) > 10 and pet_data[10] else 'ندارد'}
داروها: {pet_data[11] if len(pet_data) > 11 and pet_data[11] else 'ندارد'}
وضعیت واکسن: {pet_data[12] if len(pet_data) > 12 and pet_data[12] else 'نامشخص'}
        """
    else:
        # Handle dict format
        return f"""
نام: {pet_data.get('name', 'نامشخص')}
نوع: {pet_data.get('species', 'نامشخص')}
نژاد: {pet_data.get('breed', 'نامشخص')}
سن: {format_age(pet_data.get('age_years', 0), pet_data.get('age_months', 0))}
وزن: {format_weight(pet_data.get('weight'))}
جنسیت: {pet_data.get('gender', 'نامشخص')}
عقیم شده: {'بله' if pet_data.get('is_neutered') else 'خیر'}
بیماری‌ها: {pet_data.get('diseases', 'ندارد')}
داروها: {pet_data.get('medications', 'ندارد')}
وضعیت واکسن: {pet_data.get('vaccine_status', 'نامشخص')}
        """

def format_comprehensive_health_data(health_logs):
    """📊 Format comprehensive health data with trends"""
    if not health_logs:
        return "هیچ داده سلامتی موجود نیست"
    
    health_data = f"📊 **تاریخچه سلامت ({len(health_logs)} ثبت):**\n\n"
    
    for i, log in enumerate(health_logs[:10], 1):  # Show last 10 logs
        # Handle both tuple and dict formats
        if isinstance(log, (list, tuple)):
            date = log[2] if len(log) > 2 else 'نامشخص'
            weight = log[3] if len(log) > 3 else None
            food_type = log[4] if len(log) > 4 else None
            mood = log[5] if len(log) > 5 else None
            stool = log[6] if len(log) > 6 else None
            symptoms = log[7] if len(log) > 7 else None
            sleep_hours = log[8] if len(log) > 8 else None
            medication = log[9] if len(log) > 9 else None
            activity = log[10] if len(log) > 10 else None
            notes = log[11] if len(log) > 11 else None
        else:
            date = log.get('date', 'نامشخص')
            weight = log.get('weight')
            food_type = log.get('food_type')
            mood = log.get('mood')
            stool = log.get('stool_info')
            symptoms = log.get('symptoms')
            sleep_hours = log.get('sleep_hours')
            medication = log.get('medication_taken')
            activity = log.get('activity_level')
            notes = log.get('notes')
        
        health_data += f"""**ثبت {english_to_persian_numbers(str(i))} ({date}):**
• وزن: {format_weight(weight) if weight else 'ثبت نشد'}
• نوع غذا: {food_type or 'نامشخص'}
• حالت: {mood or 'نامشخص'}
• مدفوع: {stool or 'نامشخص'}
• علائم: {symptoms or 'ندارد'}
• خواب: {english_to_persian_numbers(str(sleep_hours)) + ' ساعت' if sleep_hours else 'نامشخص'}
• دارو: {'مصرف شد' if medication else 'مصرف نشد'}
• فعالیت: {activity or 'نامشخص'}
• یادداشت: {notes or 'ندارد'}
---
        """
    
    return health_data

def analyze_health_trends_comprehensive(health_logs):
    """📈 Comprehensive health trend analysis"""
    if len(health_logs) < 3:
        return "داده کافی برای تحلیل روند موجود نیست"
    
    trends = []
    
    # Weight trend analysis
    weights = []
    for log in health_logs[:7]:  # Last week
        if isinstance(log, (list, tuple)):
            weight = log[3] if len(log) > 3 and log[3] else None
        else:
            weight = log.get('weight')
        if weight:
            weights.append(weight)
    
    if len(weights) >= 3:
        recent_avg = sum(weights[:3]) / 3
        older_avg = sum(weights[-3:]) / 3
        weight_change = ((recent_avg - older_avg) / older_avg) * 100 if older_avg > 0 else 0
        
        if weight_change > 5:
            trends.append("📈 **روند وزن:** افزایش قابل توجه (+{:.1f}%)".format(weight_change))
        elif weight_change < -5:
            trends.append("📉 **روند وزن:** کاهش قابل توجه ({:.1f}%)".format(weight_change))
        else:
            trends.append("➡️ **روند وزن:** ثابت و پایدار")
    
    # Mood trend analysis
    moods = []
    for log in health_logs[:7]:
        if isinstance(log, (list, tuple)):
            mood = log[5] if len(log) > 5 else None
        else:
            mood = log.get('mood')
        if mood:
            moods.append(mood)
    
    if moods:
        positive_moods = sum(1 for mood in moods if mood in ["شاد و پرانرژی", "عادی"])
        mood_percentage = (positive_moods / len(moods)) * 100
        
        if mood_percentage >= 80:
            trends.append("😊 **روند حالت:** مثبت و پایدار ({:.0f}% مثبت)".format(mood_percentage))
        elif mood_percentage >= 60:
            trends.append("😐 **روند حالت:** متوسط ({:.0f}% مثبت)".format(mood_percentage))
        else:
            trends.append("😟 **روند حالت:** نگران‌کننده ({:.0f}% مثبت)".format(mood_percentage))
    
    # Activity trend analysis
    activities = []
    for log in health_logs[:7]:
        if isinstance(log, (list, tuple)):
            activity = log[10] if len(log) > 10 else None
        else:
            activity = log.get('activity_level')
        if activity:
            activities.append(activity)
    
    if activities:
        high_activities = sum(1 for activity in activities if activity == "زیاد")
        low_activities = sum(1 for activity in activities if activity == "کم")
        
        if high_activities > low_activities:
            trends.append("🏃 **روند فعالیت:** فعال و پرانرژی")
        elif low_activities > high_activities:
            trends.append("😴 **روند فعالیت:** کم و نیازمند توجه")
        else:
            trends.append("🚶 **روند فعالیت:** متوسط و طبیعی")
    
    # Symptoms trend analysis
    symptoms_count = 0
    for log in health_logs[:7]:
        if isinstance(log, (list, tuple)):
            symptoms = log[7] if len(log) > 7 else None
        else:
            symptoms = log.get('symptoms')
        if symptoms and symptoms != "ندارد":
            symptoms_count += 1
    
    if symptoms_count == 0:
        trends.append("✅ **روند علائم:** هیچ علامت نگران‌کننده‌ای نیست")
    elif symptoms_count <= 2:
        trends.append("🟡 **روند علائم:** علائم خفیف و قابل کنترل")
    else:
        trends.append("🔴 **روند علائم:** علائم مکرر - نیاز به بررسی")
    
    return "\n".join(trends) if trends else "روندهای خاصی شناسایی نشد"

def get_breed_specific_insights(breed, species):
    """🧬 Get breed-specific health insights"""
    breed_data = {
        "گربه": {
            "پرشین": {
                "common_issues": ["مشکلات تنفسی", "بیماری کلیه پلی‌کیستیک", "مشکلات چشم"],
                "care_tips": ["تمیز کردن روزانه چشم", "کنترل وزن", "آب کافی"],
                "lifespan": "12-17 سال",
                "special_notes": "نیاز به مراقبت ویژه از مو و تنفس"
            },
            "DSH": {
                "common_issues": ["چاقی", "مشکلات دندان", "کرم‌های انگلی"],
                "care_tips": ["کنترل وزن", "تمیز کردن دندان", "واکسیناسیون منظم"],
                "lifespan": "13-17 سال",
                "special_notes": "نژاد مقاوم با نیازهای استاندارد"
            }
        },
        "سگ": {
            "گلدن رتریور": {
                "common_issues": ["دیسپلازی هیپ", "سرطان", "مشکلات قلبی"],
                "care_tips": ["ورزش منظم", "کنترل وزن", "بررسی دوره‌ای قلب"],
                "lifespan": "10-12 سال",
                "special_notes": "نیاز به فعالیت زیاد و تغذیه کنترل شده"
            },
            "لابرادور": {
                "common_issues": ["چاقی", "دیسپلازی آرنج", "مشکلات چشم"],
                "care_tips": ["کنترل دقیق غذا", "ورزش روزانه", "بررسی چشم"],
                "lifespan": "10-14 سال",
                "special_notes": "تمایل زیاد به خوردن - کنترل وزن ضروری"
            }
        }
    }
    
    species_data = breed_data.get(species, {})
    breed_info = species_data.get(breed, {})
    
    if not breed_info:
        return f"اطلاعات خاص نژاد {breed} در دسترس نیست"
    
    insights = f"""🧬 **بینش‌های نژاد {breed}:**

⚠️ **مشکلات شایع:**
{chr(10).join(f'• {issue}' for issue in breed_info.get('common_issues', []))}

💡 **نکات مراقبت:**
{chr(10).join(f'• {tip}' for tip in breed_info.get('care_tips', []))}

⏰ **طول عمر متوسط:** {breed_info.get('lifespan', 'نامشخص')}

📝 **نکات ویژه:** {breed_info.get('special_notes', 'ندارد')}
    """
    
    return insights

def format_age(years, months):
    """Format age in Persian"""
    if not years and not months:
        return "نامشخص"
    
    age_parts = []
    if years:
        age_parts.append(f"{english_to_persian_numbers(str(years))} سال")
    if months:
        age_parts.append(f"{english_to_persian_numbers(str(months))} ماه")
    
    return " و ".join(age_parts) if age_parts else "نامشخص"

def format_weight(weight):
    """Format weight in Persian"""
    if not weight:
        return "نامشخص"
    
    if weight < 1:
        return f"{english_to_persian_numbers(str(int(weight * 1000)))} گرم"
    else:
        return f"{english_to_persian_numbers(str(weight))} کیلوگرم"
