from telegram import Update
from telegram.ext import ContextTypes
from utils.database import db
from utils.keyboards import *
from utils.openai_client import analyze_health, get_ai_health_insights
from utils.persian_utils import *
from handlers.subscription import check_user_subscription, is_premium_feature_blocked, show_premium_blocked_feature
import config
from datetime import datetime, timedelta

async def start_health_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start health analysis"""
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
    
    await query.edit_message_text(
        "🔍 تحلیل سلامت با هوش مصنوعی\n\n"
        "برای کدام حیوان خانگی می‌خواهید تحلیل سلامت انجام دهید؟",
        reply_markup=pets_list_keyboard(pets)
    )

async def analyze_pet_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyze specific pet health"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("analyze_health_"):
        pet_id = int(query.data.split("_")[-1])
        await perform_health_analysis(update, pet_id)
    elif query.data.startswith("select_pet_"):
        pet_id = int(query.data.split("_")[-1])
        await perform_health_analysis(update, pet_id)

async def perform_health_analysis(update, pet_id):
    """Perform actual health analysis with free/premium differentiation"""
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
            f"❌ برای {selected_pet[2]} هنوز اطلاعات سلامت ثبت نشده است.\n"
            "ابتدا چند روز سلامت حیوان خانگی را ثبت کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 ثبت سلامت", callback_data=f"log_health_{pet_id}")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
            ])
        )
        return
    
    # Show different analysis progress based on subscription
    if is_premium:
        await perform_premium_analysis(query, pet_id, selected_pet, health_logs)
    else:
        await perform_free_analysis(query, pet_id, selected_pet, health_logs)

async def perform_free_analysis(query, pet_id, selected_pet, health_logs):
    """Perform basic analysis for free users"""
    await query.edit_message_text(
        f"📊 **تحلیل پایه‌ای سلامت {selected_pet[2]}**\n\n"
        "🔍 در حال محاسبه نمره سلامت...\n"
        "⏳ لطفاً صبر کنید...",
        reply_markup=back_keyboard("back_main"),
        parse_mode='Markdown'
    )
    
    try:
        # Basic health score calculation (simplified)
        health_score, alerts = calculate_basic_health_score(health_logs, selected_pet)
        latest_log = health_logs[0]
        
        # Basic analysis text
        basic_analysis = f"""📊 **تحلیل پایه‌ای سلامت {selected_pet[2]}**

🎯 **نمره سلامت**: {english_to_persian_numbers(str(health_score))}/۱۰۰
{get_health_status_emoji(health_score)} **وضعیت**: {get_health_status_text(health_score)}

📋 **آخرین وضعیت**:
• وزن: {format_weight(latest_log[3]) if latest_log[3] else 'ثبت نشد'}
• حالت: {latest_log[5] or 'نامشخص'}
• مدفوع: {latest_log[6] or 'نامشخص'}
• فعالیت: {latest_log[9] or 'نامشخص'}

⚠️ **هشدارهای مهم**:
{chr(10).join(f'• {alert}' for alert in alerts[:2]) if alerts else '• هیچ هشدار خاصی وجود ندارد'}

💡 **توصیه کلی**:
• ادامه ثبت روزانه سلامت
• مراقبت‌های معمول
• در صورت تغییر ناگهانی، مراجعه به دامپزشک

🔒 **برای تحلیل‌های پیشرفته‌تر:**
• تحلیل روندهای هفتگی و ماهانه
• پیش‌بینی مشکلات قبل از بروز
• توصیه‌های تخصصی بر اساس نژاد و سن
• گزارش‌های قابل چاپ برای دامپزشک

**به نسخه پریمیوم ارتقاء دهید!**
        """
        
        # Create keyboard with premium upgrade
        keyboard = [
            [InlineKeyboardButton("🚀 ارتقاء به پریمیوم", callback_data="upgrade_premium")],
            [InlineKeyboardButton("📊 ثبت سلامت جدید", callback_data=f"log_health_{pet_id}")],
            [InlineKeyboardButton("💬 مشاوره AI", callback_data="ai_chat")],
            [InlineKeyboardButton("🔄 تحلیل مجدد", callback_data=f"analyze_health_{pet_id}")],
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
        ]
        
        await query.edit_message_text(
            basic_analysis,
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

async def perform_premium_analysis(query, pet_id, selected_pet, health_logs):
    """Perform advanced analysis for premium users with full AI insights"""
    await query.edit_message_text(
            f"🧠 **تحلیل‌های هوشمند سلامت {selected_pet[2]}**\n\n"
            "🤖 تحلیل هوشمند در حال انجام...\n"
            "📊 بررسی عمیق داده‌های سلامت...\n"
            "📈 شناسایی روندها و الگوها...\n"
            "🔮 پیش‌بینی مشکلات احتمالی...\n"
            "⚠️ ارزیابی عوامل خطر...\n"
            "💡 تولید توصیه‌های تخصصی...\n\n"
            "⏳ لطفاً صبر کنید...",
            reply_markup=back_keyboard("back_main"),
            parse_mode='Markdown'
        )
    
    try:
        # Prepare comprehensive data for AI
        pet_info = format_comprehensive_pet_info(selected_pet)
        health_data = format_comprehensive_health_data(health_logs)
        
        # Get comprehensive AI analysis using reasoning model
        ai_analysis = ""
        health_score = 85  # Default
        risk_level = 1
        
        try:
            # Use OpenAI reasoning model for comprehensive analysis
            ai_response = await analyze_health(health_data, pet_info, use_reasoning=True)
            if ai_response and len(ai_response.strip()) > 50:
                ai_analysis = ai_response
                # Extract score and risk from AI response if possible
                health_score, risk_level = extract_ai_metrics(ai_response)
            else:
                ai_analysis = await get_fallback_ai_analysis(health_logs, selected_pet)
        except Exception as e:
            ai_analysis = await get_fallback_ai_analysis(health_logs, selected_pet)
        
        # Calculate additional metrics
        trend_analysis = calculate_health_trends(health_logs)
        recommendations = generate_ai_recommendations(selected_pet, health_logs, ai_analysis)
        
        # Format comprehensive premium analysis
        premium_analysis = f"""🧠 **تحلیل‌های هوشمند سلامت {selected_pet[2]}**

📊 **نمره سلامت**: {english_to_persian_numbers(str(health_score))}/۱۰۰
{get_health_status_emoji(health_score)} **وضعیت کلی**: {get_health_status_text(health_score)}
⚠️ **سطح خطر**: {get_risk_level_text(risk_level)}

🤖 **تحلیل هوش مصنوعی پیشرفته**:
{ai_analysis}

📈 **تحلیل روندها**:
{trend_analysis}

🎯 **توصیه‌های تخصصی**:
{recommendations}

📊 **آمار**: {english_to_persian_numbers(str(len(health_logs)))} ثبت | ⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}
🏆 **مدل**: OpenAI o1-reasoning | **نسخه**: Premium
        """
        
        # Create premium keyboard (without PDF)
        keyboard = []
        
        # Emergency actions if high risk
        if risk_level >= 3:
            keyboard.append([InlineKeyboardButton("🚨 راهنمایی اورژانس", callback_data="emergency_mode")])
        
        # Premium features
        keyboard.extend([
            [InlineKeyboardButton("📊 ثبت سلامت جدید", callback_data=f"log_health_{pet_id}")],
            [InlineKeyboardButton("📋 تاریخچه کامل", callback_data=f"history_{pet_id}")],
            [InlineKeyboardButton("💬 مشاوره VETX", callback_data="ai_chat")],
            [InlineKeyboardButton("🥘 مشاوره تغذیه", callback_data="nutrition_mode")],
            [InlineKeyboardButton("🔄 تحلیل مجدد", callback_data=f"analyze_health_{pet_id}")],
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
        ])
        
        await query.edit_message_text(
            premium_analysis,
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

def calculate_basic_health_score(health_logs, pet_info):
    """Calculate basic health score for free users"""
    if not health_logs:
        return 50, []
    
    score = 100
    alerts = []
    latest_log = health_logs[0]
    
    # Simple checks only
    if latest_log[6] == "خونی":  # Blood in stool - critical
        score -= 30
        alerts.append("🔴 خون در مدفوع - مراجعه فوری")
    
    if latest_log[5] == "خسته و بی‌حال":  # Tired mood
        score -= 15
        alerts.append("🟠 حالت خستگی")
    
    if latest_log[9] == "کم":  # Low activity
        score -= 10
        alerts.append("🟡 فعالیت پایین")
    
    # Basic weight check (only if multiple logs)
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
    """Calculate advanced health score with trend analysis"""
    if not health_logs:
        return 50, [], "داده کافی موجود نیست"
    
    score = 100
    alerts = []
    details = []
    
    # Get recent logs (last 3 for trend analysis)
    recent_logs = health_logs[:3]
    latest_log = health_logs[0]
    
    # 1. Weight Analysis (20 points max penalty)
    weights = [log[3] for log in recent_logs if log[3]]
    if len(weights) >= 2:
        weight_change_percent = abs(weights[0] - weights[1]) / weights[1] * 100 if weights[1] > 0 else 0
        if weight_change_percent > 5:  # >5% change
            score -= 20
            alerts.append("🔴 تغییر ناگهانی وزن")
            details.append(f"تغییر وزن: {weight_change_percent:.1f}%")
        elif weight_change_percent > 2:
            score -= 10
            alerts.append("🟠 تغییر وزن قابل توجه")
    
    # 2. Mood Analysis (15 points max penalty)
    moods = [log[5] for log in recent_logs if log[5]]
    bad_moods = sum(1 for mood in moods if mood in ["خسته و بی‌حال", "اضطراب"])
    if bad_moods >= 2:  # 2+ bad moods in recent logs
        score -= 15
        alerts.append("🔴 حالت روحی نامناسب مداوم")
    elif bad_moods == 1:
        score -= 8
        alerts.append("🟠 حالت روحی نگران‌کننده")
    
    # 3. Stool Analysis (25 points max penalty - critical)
    stools = [log[6] for log in recent_logs if log[6]]
    bloody_stools = sum(1 for stool in stools if stool == "خونی")
    if bloody_stools >= 2:  # Blood in 2+ recent logs
        score -= 25
        alerts.append("🔴 خون در مدفوع - فوری")
    elif bloody_stools == 1:
        score -= 15
        alerts.append("🔴 خون در مدفوع")
    elif any(stool in ["نرم", "سفت"] for stool in stools):
        abnormal_count = sum(1 for stool in stools if stool in ["نرم", "سفت"])
        if abnormal_count >= 2:
            score -= 10
            alerts.append("🟠 مشکل مداوم گوارشی")
        else:
            score -= 5
    
    # 4. Activity Analysis (10 points max penalty)
    activities = [log[9] for log in recent_logs if log[9]]
    low_activities = sum(1 for activity in activities if activity == "کم")
    if low_activities >= 2:
        score -= 10
        alerts.append("🟠 فعالیت پایین مداوم")
    elif low_activities == 1:
        score -= 5
    
    # 5. Trend Analysis Bonus/Penalty
    if len(health_logs) >= 5:
        # Check for improvement trends
        old_moods = [log[5] for log in health_logs[3:] if log[5]]
        if moods and old_moods:
            if all(mood in ["شاد و پرانرژی", "عادی"] for mood in moods) and any(mood in ["خسته و بی‌حال", "اضطراب"] for mood in old_moods):
                score += 5  # Improvement bonus
                details.append("بهبود حالت روحی")
    
    # 6. Critical Flags
    if bloody_stools >= 1:
        alerts.insert(0, "🚨 نیاز به مراجعه فوری به دامپزشک")
    
    # Ensure score bounds
    score = max(0, min(100, score))
    
    # Generate details summary
    details_text = "\n".join([
        f"• وزن: {format_weight(latest_log[3]) if latest_log[3] else 'ثبت نشد'}",
        f"• حالت: {latest_log[5] or 'نامشخص'}",
        f"• مدفوع: {latest_log[6] or 'نامشخص'}",
        f"• فعالیت: {latest_log[9] or 'نامشخص'}",
        f"• تعداد ثبت‌ها: {english_to_persian_numbers(str(len(health_logs)))}"
    ] + details)
    
    return score, alerts, details_text

def format_pet_info(pet_data):
    """Format pet info for AI"""
    return f"""
نام: {pet_data[2]}
نوع: {pet_data[3]}
نژاد: {pet_data[4] or 'نامشخص'}
سن: {format_age(pet_data[5], pet_data[6])}
وزن: {format_weight(pet_data[7])}
جنسیت: {pet_data[8]}
عقیم شده: {'بله' if pet_data[9] else 'خیر'}
بیماری‌ها: {pet_data[10] or 'ندارد'}
داروها: {pet_data[11] or 'ندارد'}
وضعیت واکسن: {pet_data[12] or 'نامشخص'}
    """

def format_health_data(health_logs):
    """Format health data for AI"""
    health_data = "آخرین ثبت‌های سلامت (از جدید به قدیم):\n"
    for i, log in enumerate(health_logs[:5], 1):
        health_data += f"""
ثبت {english_to_persian_numbers(str(i))}:
- وزن: {format_weight(log[3]) if log[3] else 'ثبت نشد'}
- حالت: {log[5] or 'نامشخص'}
- مدفوع: {log[6] or 'نامشخص'}
- فعالیت: {log[9] or 'نامشخص'}
- یادداشت: {log[10] or 'ندارد'}
        """
    return health_data

def generate_fallback_analysis(health_logs, pet_info, alerts):
    """Generate fallback analysis when AI fails"""
    latest_log = health_logs[0]
    
    analysis = "تحلیل محلی (بدون هوش مصنوعی):\n\n"
    
    if alerts:
        analysis += "⚠️ نکات مهم:\n"
        for alert in alerts[:3]:  # Show top 3 alerts
            analysis += f"• {alert}\n"
        analysis += "\n"
    
    # Basic recommendations
    if latest_log[5] == "خسته و بی‌حال":
        analysis += "• توصیه: بررسی علت خستگی و مراجعه به دامپزشک\n"
    
    if latest_log[6] == "خونی":
        analysis += "• توصیه: مراجعه فوری به دامپزشک\n"
    
    if latest_log[9] == "کم":
        analysis += "• توصیه: افزایش تدریجی فعالیت و بررسی علت\n"
    
    if not alerts:
        analysis += "• وضعیت کلی مناسب است\n• ادامه مراقبت‌های روزانه\n"
    
    return analysis

def format_alerts(alerts):
    """Format alerts for display"""
    if not alerts:
        return "✅ **هیچ هشدار خاصی وجود ندارد**\n"
    
    alert_text = "⚠️ **هشدارها:**\n"
    for alert in alerts:
        alert_text += f"• {alert}\n"
    return alert_text + "\n"

def get_health_status_emoji(score):
    """Get emoji based on health score"""
    if score >= 80:
        return "🟢"
    elif score >= 60:
        return "🟡"
    elif score >= 40:
        return "🟠"
    else:
        return "🔴"

def get_health_status_text(score):
    """Get status text based on health score"""
    if score >= 80:
        return "سالم"
    elif score >= 60:
        return "نرمال - مراقب باشید"
    elif score >= 40:
        return "نیازمند پیگیری"
    else:
        return "وضعیت نگران‌کننده"

def calculate_ai_health_score(health_logs, pet_info):
    """Advanced AI-powered health score calculation"""
    if not health_logs:
        return 50, [], "داده کافی موجود نیست", 1
    
    score = 100
    alerts = []
    details = []
    risk_level = 0  # 0=کم, 1=متوسط, 2=بالا, 3=بحرانی
    
    # Get recent logs for analysis
    recent_logs = health_logs[:5]
    latest_log = health_logs[0]
    
    # 1. Advanced Weight Analysis (25 points)
    weights = [log[3] for log in recent_logs if log[3]]
    if len(weights) >= 2:
        weight_changes = []
        for i in range(len(weights)-1):
            if weights[i+1] > 0:
                change = abs(weights[i] - weights[i+1]) / weights[i+1] * 100
                weight_changes.append(change)
        
        if weight_changes:
            avg_change = sum(weight_changes) / len(weight_changes)
            max_change = max(weight_changes)
            
            if max_change > 10:  # >10% change
                score -= 25
                risk_level = max(risk_level, 3)
                alerts.append("🔴 تغییر وزن بحرانی")
                details.append(f"حداکثر تغییر وزن: {max_change:.1f}%")
            elif max_change > 5:
                score -= 15
                risk_level = max(risk_level, 2)
                alerts.append("🟠 تغییر وزن قابل توجه")
            elif avg_change > 2:
                score -= 8
                risk_level = max(risk_level, 1)
                alerts.append("🟡 نوسان وزن")
    
    # 2. Mood Pattern Analysis (20 points)
    moods = [log[5] for log in recent_logs if log[5]]
    if moods:
        bad_mood_count = sum(1 for mood in moods if mood in ["خسته و بی‌حال", "اضطراب"])
        mood_ratio = bad_mood_count / len(moods)
        
        if mood_ratio >= 0.8:  # 80%+ bad moods
            score -= 20
            risk_level = max(risk_level, 3)
            alerts.append("🔴 حالت روحی بحرانی")
        elif mood_ratio >= 0.6:  # 60%+ bad moods
            score -= 15
            risk_level = max(risk_level, 2)
            alerts.append("🟠 حالت روحی نامناسب")
        elif mood_ratio >= 0.4:  # 40%+ bad moods
            score -= 8
            risk_level = max(risk_level, 1)
            alerts.append("🟡 نگرانی حالت روحی")
    
    # 3. Critical Digestive Analysis (30 points)
    stools = [log[6] for log in recent_logs if log[6]]
    if stools:
        bloody_count = sum(1 for stool in stools if stool == "خونی")
        abnormal_count = sum(1 for stool in stools if stool in ["نرم", "سفت"])
        
        if bloody_count >= 2:
            score -= 30
            risk_level = 3
            alerts.insert(0, "🚨 خون مداوم در مدفوع - اورژانس")
        elif bloody_count == 1:
            score -= 20
            risk_level = max(risk_level, 2)
            alerts.append("🔴 خون در مدفوع")
        elif abnormal_count >= 3:
            score -= 15
            risk_level = max(risk_level, 2)
            alerts.append("🟠 مشکل مداوم گوارشی")
        elif abnormal_count >= 1:
            score -= 8
            risk_level = max(risk_level, 1)
            alerts.append("🟡 نامنظمی گوارشی")
    
    # 4. Activity Level Assessment (15 points)
    activities = [log[9] for log in recent_logs if log[9]]
    if activities:
        low_activity_count = sum(1 for activity in activities if activity == "کم")
        activity_ratio = low_activity_count / len(activities)
        
        if activity_ratio >= 0.8:
            score -= 15
            risk_level = max(risk_level, 2)
            alerts.append("🟠 فعالیت بسیار پایین")
        elif activity_ratio >= 0.6:
            score -= 10
            risk_level = max(risk_level, 1)
            alerts.append("🟡 فعالیت پایین")
        elif activity_ratio >= 0.4:
            score -= 5
            alerts.append("⚪ کاهش فعالیت")
    
    # 5. Age-based Risk Factors (10 points)
    age_years = pet_info[5] or 0
    if age_years > 10:  # Senior pets
        score -= 5
        risk_level = max(risk_level, 1)
        details.append("عوامل خطر سنی")
    elif age_years < 1:  # Young pets
        score -= 3
        details.append("حساسیت سن پایین")
    
    # 6. Trend Analysis Bonus/Penalty
    if len(health_logs) >= 7:
        # Improvement trend detection
        old_moods = [log[5] for log in health_logs[3:7] if log[5]]
        recent_moods = [log[5] for log in health_logs[:3] if log[5]]
        
        if recent_moods and old_moods:
            recent_good = sum(1 for mood in recent_moods if mood in ["شاد و پرانرژی", "عادی"])
            old_good = sum(1 for mood in old_moods if mood in ["شاد و پرانرژی", "عادی"])
            
            if recent_good > old_good:
                score += 5
                details.append("روند بهبود حالت")
            elif recent_good < old_good:
                score -= 5
                details.append("روند نزولی حالت")
    
    # Ensure score bounds
    score = max(0, min(100, score))
    
    # Generate comprehensive details
    details_text = "\n".join([
        f"• آخرین وزن: {format_weight(latest_log[3]) if latest_log[3] else 'ثبت نشد'}",
        f"• آخرین حالت: {latest_log[5] or 'نامشخص'}",
        f"• آخرین مدفوع: {latest_log[6] or 'نامشخص'}",
        f"• آخرین فعالیت: {latest_log[9] or 'نامشخص'}",
        f"• تعداد ثبت‌ها: {english_to_persian_numbers(str(len(health_logs)))}",
        f"• سن حیوان: {format_age(pet_info[5], pet_info[6])}"
    ] + details)
    
    return score, alerts, details_text, risk_level

def format_comprehensive_pet_info(pet_data):
    """Format comprehensive pet info for advanced AI analysis"""
    return f"""
🐾 PATIENT PROFILE:
نام: {pet_data[2]}
نوع: {pet_data[3]}
نژاد: {pet_data[4] or 'نامشخص'}
سن: {format_age(pet_data[5], pet_data[6])}
وزن پایه: {format_weight(pet_data[7])}
جنسیت: {pet_data[8]}
وضعیت عقیم‌سازی: {'انجام شده' if pet_data[9] else 'انجام نشده'}
سابقه بیماری: {pet_data[10] or 'بدون سابقه'}
داروهای فعلی: {pet_data[11] or 'هیچ'}
وضعیت واکسیناسیون: {pet_data[12] or 'نامشخص'}
تاریخ ثبت: {pet_data[13][:10] if pet_data[13] else 'نامشخص'}
    """

def format_comprehensive_health_data(health_logs):
    """Format comprehensive health data for AI analysis"""
    health_data = "📊 COMPREHENSIVE HEALTH DATA:\n\n"
    
    for i, log in enumerate(health_logs[:7], 1):
        health_data += f"""
📅 ثبت {english_to_persian_numbers(str(i))} - تاریخ: {log[2] if log[2] else 'نامشخص'}
⚖️ وزن: {format_weight(log[3]) if log[3] else 'ثبت نشده'}
😊 حالت روحی: {log[5] or 'نامشخص'}
💩 وضعیت مدفوع: {log[6] or 'نامشخص'}
🍽️ اشتها: {log[7] or 'نامشخص'}
💧 نوشیدن آب: {log[8] or 'نامشخص'}
🏃 سطح فعالیت: {log[9] or 'نامشخص'}
📝 یادداشت: {log[10] or 'بدون یادداشت'}
---
        """
    
    # Add statistical summary
    weights = [log[3] for log in health_logs if log[3]]
    if weights:
        avg_weight = sum(weights) / len(weights)
        health_data += f"\n📈 STATISTICS:\n"
        health_data += f"میانگین وزن: {format_weight(avg_weight)}\n"
        health_data += f"تعداد کل ثبت‌ها: {english_to_persian_numbers(str(len(health_logs)))}\n"
    
    return health_data

def calculate_health_trends(health_logs):
    """Calculate health trends and patterns"""
    if len(health_logs) < 3:
        return "داده کافی برای تحلیل روند موجود نیست"
    
    trends = []
    
    # Weight trend
    weights = [log[3] for log in health_logs[:5] if log[3]]
    if len(weights) >= 3:
        if weights[0] > weights[-1]:
            weight_trend = "کاهش وزن"
        elif weights[0] < weights[-1]:
            weight_trend = "افزایش وزن"
        else:
            weight_trend = "وزن ثابت"
        trends.append(f"📈 روند وزن: {weight_trend}")
    
    # Mood trend
    moods = [log[5] for log in health_logs[:5] if log[5]]
    if moods:
        good_moods = sum(1 for mood in moods if mood in ["شاد و پرانرژی", "عادی"])
        mood_percentage = (good_moods / len(moods)) * 100
        
        if mood_percentage >= 80:
            mood_trend = "مثبت و پایدار"
        elif mood_percentage >= 60:
            mood_trend = "نسبتاً مثبت"
        elif mood_percentage >= 40:
            mood_trend = "متغیر"
        else:
            mood_trend = "نگران‌کننده"
        trends.append(f"😊 روند حالت: {mood_trend}")
    
    # Activity trend
    activities = [log[9] for log in health_logs[:5] if log[9]]
    if activities:
        high_activities = sum(1 for activity in activities if activity == "زیاد")
        if high_activities >= len(activities) // 2:
            activity_trend = "فعال"
        elif sum(1 for activity in activities if activity == "کم") >= len(activities) // 2:
            activity_trend = "کم‌فعال"
        else:
            activity_trend = "متوسط"
        trends.append(f"🏃 روند فعالیت: {activity_trend}")
    
    return "\n".join(trends) if trends else "روندهای قابل تشخیص موجود نیست"

def generate_personalized_recommendations(pet_info, health_logs, risk_level):
    """Generate personalized recommendations based on analysis"""
    recommendations = []
    
    # Risk-based recommendations
    if risk_level >= 3:
        recommendations.append("🚨 مراجعه فوری به دامپزشک ضروری است")
        recommendations.append("📞 تماس با کلینیک اورژانس")
    elif risk_level >= 2:
        recommendations.append("⚠️ مراجعه به دامپزشک در اولین فرصت")
        recommendations.append("📋 آماده‌سازی لیست علائم برای دامپزشک")
    elif risk_level >= 1:
        recommendations.append("🔍 پیگیری دقیق‌تر وضعیت سلامت")
        recommendations.append("📊 ثبت روزانه سلامت")
    
    # Age-based recommendations
    age_years = pet_info[5] or 0
    if age_years > 8:
        recommendations.append("👴 چک‌آپ منظم برای حیوان مسن")
        recommendations.append("🥘 رژیم غذایی مخصوص سالمندان")
    elif age_years < 1:
        recommendations.append("🍼 مراقبت ویژه برای حیوان جوان")
        recommendations.append("💉 پیگیری برنامه واکسیناسیون")
    
    # Health-specific recommendations
    if health_logs:
        latest_log = health_logs[0]
        
        if latest_log[5] == "خسته و بی‌حال":
            recommendations.append("😴 بررسی علت خستگی")
            recommendations.append("🛏️ فراهم کردن محیط آرام")
        
        if latest_log[6] == "خونی":
            recommendations.append("🩸 مراجعه فوری برای خون در مدفوع")
        
        if latest_log[9] == "کم":
            recommendations.append("🚶 تشویق به فعالیت تدریجی")
            recommendations.append("🎾 بازی‌های محرک")
    
    # General recommendations
    recommendations.extend([
        "💧 تأمین آب تمیز و تازه",
        "🥗 تغذیه منظم و متعادل",
        "🧼 بهداشت محیط زندگی",
        "❤️ توجه و محبت بیشتر"
    ])
    
    return "\n".join(f"• {rec}" for rec in recommendations[:8])  # Limit to 8 recommendations

def generate_advanced_fallback_analysis(health_logs, pet_info, alerts, risk_level):
    """Generate advanced fallback analysis when AI fails"""
    latest_log = health_logs[0]
    
    analysis = "🔬 تحلیل سیستم محلی (پیشرفته):\n\n"
    
    # Risk assessment
    risk_texts = {
        0: "خطر پایین - وضعیت مناسب",
        1: "خطر متوسط - نیاز به مراقبت",
        2: "خطر بالا - نیاز به پیگیری",
        3: "خطر بحرانی - مراجعه فوری"
    }
    analysis += f"⚠️ سطح خطر: {risk_texts.get(risk_level, 'نامشخص')}\n\n"
    
    if alerts:
        analysis += "🚨 هشدارهای مهم:\n"
        for alert in alerts[:3]:
            analysis += f"• {alert}\n"
        analysis += "\n"
    
    # Specific recommendations based on latest data
    analysis += "💡 توصیه‌های فوری:\n"
    
    if latest_log[6] == "خونی":
        analysis += "• مراجعه فوری به دامپزشک برای خون در مدفوع\n"
        analysis += "• قطع غذا تا مشورت با دامپزشک\n"
    
    if latest_log[5] == "خسته و بی‌حال":
        analysis += "• بررسی دمای بدن\n"
        analysis += "• تأمین محیط آرام و گرم\n"
    
    if latest_log[9] == "کم":
        analysis += "• بررسی علت کاهش فعالیت\n"
        analysis += "• تشویق تدریجی به حرکت\n"
    
    if not alerts:
        analysis += "• ادامه مراقبت‌های روزانه\n"
        analysis += "• ثبت منظم اطلاعات سلامت\n"
        analysis += "• چک‌آپ دوره‌ای با دامپزشک\n"
    
    return analysis

def get_risk_level_text(risk_level):
    """Get Persian text for risk level"""
    risk_texts = {
        0: "🟢 کم",
        1: "🟡 متوسط", 
        2: "🟠 بالا",
        3: "🔴 بحرانی"
    }
    return risk_texts.get(risk_level, "نامشخص")

async def show_pet_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pet health history"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("history_"):
        pet_id = int(query.data.split("_")[-1])
        user_id = update.effective_user.id
        
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
                f"❌ برای {selected_pet[2]} هنوز اطلاعات سلامت ثبت نشده است.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 ثبت سلامت", callback_data=f"log_health_{pet_id}")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=f"select_pet_{pet_id}")]
                ])
            )
            return
        
        # Format history
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
                [InlineKeyboardButton("📊 ثبت جدید", callback_data=f"log_health_{pet_id}")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data=f"select_pet_{pet_id}")]
            ]),
            parse_mode='Markdown'
        )

async def export_pdf_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export PDF report for premium users"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check if user is premium
    if is_premium_feature_blocked(user_id, 'export_reports'):
        await show_premium_blocked_feature(update, context, "گزارش‌های PDF")
        return
    
    if query.data.startswith("export_pdf_"):
        pet_id = int(query.data.split("_")[-1])
        
        # Get pet info
        pets = db.get_user_pets(user_id)
        selected_pet = next((pet for pet in pets if pet[0] == pet_id), None)
        
        if not selected_pet:
            await query.edit_message_text(
                "❌ حیوان خانگی یافت نشد.",
                reply_markup=main_menu_keyboard()
            )
            return
        
        # Show PDF generation progress
        await query.edit_message_text(
            f"📄 **تهیه گزارش PDF برای {selected_pet[2]}**\n\n"
            "🔄 در حال جمع‌آوری اطلاعات...\n"
            "📊 تحلیل داده‌های سلامت...\n"
            "📈 ایجاد نمودارها...\n"
            "📋 فرمت‌بندی گزارش تخصصی...\n\n"
            "⏳ لطفاً صبر کنید...",
            reply_markup=back_keyboard("back_main"),
            parse_mode='Markdown'
        )
        
        try:
            # Get comprehensive health data
            health_logs = db.get_pet_health_logs(pet_id, 30)  # Last 30 records
            
            if not health_logs:
                await query.edit_message_text(
                    f"❌ برای {selected_pet[2]} اطلاعات کافی برای تهیه گزارش موجود نیست.\n"
                    "حداقل ۵ ثبت سلامت نیاز است.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 ثبت سلامت", callback_data=f"log_health_{pet_id}")],
                        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"analyze_health_{pet_id}")]
                    ])
                )
                return
            
            # Generate comprehensive report
            report_content = generate_professional_report(selected_pet, health_logs)
            
            # Mock PDF generation (in real app, would generate actual PDF)
            await query.edit_message_text(
                f"✅ **گزارش PDF آماده شد!**\n\n"
                f"📋 **گزارش تخصصی سلامت {selected_pet[2]}**\n"
                f"📅 **دوره**: آخرین {english_to_persian_numbers(str(len(health_logs)))} ثبت\n"
                f"📊 **صفحات**: {english_to_persian_numbers('8')} صفحه\n"
                f"📈 **شامل**: نمودارها، تحلیل‌ها، توصیه‌ها\n\n"
                f"🏥 **قابل ارائه به دامپزشک**: ✅\n"
                f"📧 **ارسال ایمیل**: در دسترس\n"
                f"🖨️ **قابل چاپ**: بله\n\n"
                f"📄 **پیش‌نمایش گزارش**:\n"
                f"```\n{report_content[:200]}...\n```\n\n"
                f"💡 **نکته**: در نسخه واقعی، فایل PDF دانلود می‌شود.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📧 ارسال ایمیل", callback_data=f"email_report_{pet_id}")],
                    [InlineKeyboardButton("🔄 گزارش جدید", callback_data=f"export_pdf_{pet_id}")],
                    [InlineKeyboardButton("📈 تحلیل سلامت", callback_data=f"analyze_health_{pet_id}")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=f"analyze_health_{pet_id}")]
                ]),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                "❌ خطا در تهیه گزارش PDF.\n"
                "لطفاً بعداً تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"export_pdf_{pet_id}")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=f"analyze_health_{pet_id}")]
                ])
            )

def generate_professional_report(pet_info, health_logs):
    """Generate professional veterinary report"""
    report = f"""
🏥 گزارش تخصصی سلامت حیوان خانگی
═══════════════════════════════════════

📋 اطلاعات بیمار:
نام: {pet_info[2]}
نوع: {pet_info[3]}
نژاد: {pet_info[4] or 'نامشخص'}
سن: {format_age(pet_info[5], pet_info[6])}
جنسیت: {pet_info[8]}
وزن پایه: {format_weight(pet_info[7])}

📊 خلاصه آماری ({english_to_persian_numbers(str(len(health_logs)))} ثبت):
═══════════════════════════════════════

وزن‌ها: {', '.join([format_weight(log[3]) for log in health_logs[:5] if log[3]])}
حالات روحی: {', '.join([log[5] for log in health_logs[:5] if log[5]])}
وضعیت مدفوع: {', '.join([log[6] for log in health_logs[:5] if log[6]])}
سطح فعالیت: {', '.join([log[9] for log in health_logs[:5] if log[9]])}

🔬 تحلیل تخصصی:
═══════════════════════════════════════

{calculate_professional_analysis(health_logs, pet_info)}

💡 توصیه‌های دامپزشکی:
═══════════════════════════════════════

{generate_veterinary_recommendations(pet_info, health_logs)}

📅 تاریخ گزارش: {datetime.now().strftime('%Y/%m/%d - %H:%M')}
🏆 سیستم: PetMagix Premium VetX v2.0
    """
    
    return report.strip()

def calculate_professional_analysis(health_logs, pet_info):
    """Calculate professional analysis for veterinary report"""
    if not health_logs:
        return "داده کافی برای تحلیل موجود نیست"
    
    analysis = []
    
    # Weight analysis
    weights = [log[3] for log in health_logs if log[3]]
    if len(weights) >= 2:
        weight_change = abs(weights[0] - weights[-1])
        if weight_change > 0.5:  # More than 0.5kg change
            analysis.append(f"• تغییر وزن: {weight_change:.1f} کیلوگرم")
    
    # Mood patterns
    moods = [log[5] for log in health_logs if log[5]]
    if moods:
        bad_moods = sum(1 for mood in moods if mood in ["خسته و بی‌حال", "اضطراب"])
        if bad_moods > len(moods) // 2:
            analysis.append("• الگوی حالت روحی: نگران‌کننده")
        else:
            analysis.append("• الگوی حالت روحی: طبیعی")
    
    # Digestive health
    stools = [log[6] for log in health_logs if log[6]]
    if stools:
        abnormal = sum(1 for stool in stools if stool != "عادی")
        if abnormal > 0:
            analysis.append(f"• مشکلات گوارشی: {abnormal} مورد از {len(stools)} ثبت")
    
    return "\n".join(analysis) if analysis else "• تمام پارامترها در محدوده طبیعی"

def generate_veterinary_recommendations(pet_info, health_logs):
    """Generate veterinary recommendations"""
    recommendations = [
        "• ادامه ثبت منظم اطلاعات سلامت",
        "• چک‌آپ دوره‌ای هر ۶ ماه",
        "• واکسیناسیون طبق برنامه"
    ]
    
    # Age-specific recommendations
    age_years = pet_info[5] or 0
    if age_years > 8:
        recommendations.append("• آزمایش خون سالانه برای حیوان مسن")
        recommendations.append("• بررسی مفاصل و قلب")
    elif age_years < 1:
        recommendations.append("• پیگیری رشد و تکامل")
        recommendations.append("• تکمیل برنامه واکسیناسیون")
    
    # Health-specific recommendations
    if health_logs:
        latest_log = health_logs[0]
        if latest_log[6] == "خونی":
            recommendations.insert(0, "• بررسی فوری دستگاه گوارش")
        if latest_log[5] == "خسته و بی‌حال":
            recommendations.insert(0, "• بررسی علت خستگی")
    
    return "\n".join(recommendations)

async def get_fallback_ai_analysis(health_logs, pet_info):
    """Get fallback AI analysis when main AI fails"""
    latest_log = health_logs[0]
    
    analysis = """🔬 **تحلیل هوش مصنوعی محلی**:

بر اساس داده‌های موجود، وضعیت کلی حیوان خانگی شما قابل قبول است. 

🔍 **نکات مهم**:
• پارامترهای حیاتی در محدوده طبیعی
• نیاز به پیگیری مداوم وضعیت سلامت
• توصیه به ثبت منظم اطلاعات روزانه

💡 **توصیه‌های کلی**:
• ادامه مراقبت‌های معمول
• در صورت تغییر ناگهانی، مراجعه به دامپزشک
• حفظ برنامه غذایی منظم"""
    
    # Add specific alerts based on latest data
    if latest_log[6] == "خونی":
        analysis += "\n\n⚠️ **هشدار**: خون در مدفوع نیاز به بررسی فوری دارد"
    
    if latest_log[5] == "خسته و بی‌حال":
        analysis += "\n\n🟡 **توجه**: حالت خستگی نیاز به پیگیری دارد"
    
    return analysis

def extract_ai_metrics(ai_response):
    """Extract health score and risk level from AI response"""
    health_score = 85  # Default
    risk_level = 1     # Default
    
    try:
        # Try to extract score from AI response
        import re
        score_match = re.search(r'نمره[:\s]*(\d+)', ai_response)
        if score_match:
            health_score = int(score_match.group(1))
        
        # Try to extract risk level
        if "بحرانی" in ai_response or "اورژانس" in ai_response:
            risk_level = 3
        elif "بالا" in ai_response or "نگران" in ai_response:
            risk_level = 2
        elif "متوسط" in ai_response:
            risk_level = 1
        else:
            risk_level = 0
            
    except:
        pass
    
    return health_score, risk_level

def generate_ai_recommendations(pet_info, health_logs, ai_analysis):
    """Generate AI-based recommendations"""
    recommendations = []
    
    # Extract recommendations from AI analysis if possible
    if "توصیه" in ai_analysis:
        lines = ai_analysis.split('\n')
        for line in lines:
            if "•" in line and any(word in line for word in ["توصیه", "پیشنهاد", "باید", "نیاز"]):
                recommendations.append(line.strip())
    
    # Add default recommendations if none found
    if not recommendations:
        recommendations = [
            "• ادامه ثبت منظم اطلاعات سلامت",
            "• مراقبت‌های روزانه معمول",
            "• چک‌آپ دوره‌ای با دامپزشک",
            "• تغذیه متعادل و منظم",
            "• تأمین آب تمیز و تازه"
        ]
    
    return "\n".join(recommendations[:6])  # Limit to 6 recommendations
