from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.database import db
from utils.keyboards import *
from utils.persian_utils import *
import config
from datetime import datetime, timedelta
import asyncio

async def show_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show reminders main menu"""
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
    
    # Get today's reminders with real-time logic
    today_reminders = get_smart_reminders(pets)
    
    reminder_text = "⏰ **یادآورهای هوشمند**\n\n"
    
    if today_reminders:
        reminder_text += "🔔 **امروز:**\n"
        for reminder in today_reminders:
            reminder_text += f"• {reminder}\n"
        reminder_text += "\n"
    else:
        reminder_text += "✅ همه کارها انجام شده!\n\n"
    
    # Show streaks
    streaks = get_care_streaks(pets)
    if streaks:
        reminder_text += "🔥 **رکوردهای مراقبت:**\n"
        for streak in streaks:
            reminder_text += f"• {streak}\n"
        reminder_text += "\n"
    
    reminder_text += "📋 **مدیریت یادآورها:**"
    
    await query.edit_message_text(
        reminder_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 فعال‌سازی اعلان‌ها", callback_data="enable_notifications")],
            [InlineKeyboardButton("💊 یادآور دارو", callback_data="medication_reminder")],
            [InlineKeyboardButton("💉 یادآور واکسن", callback_data="vaccine_reminder")],
            [InlineKeyboardButton("📅 برنامه هفتگی", callback_data="weekly_schedule")],
            [InlineKeyboardButton("📊 ثبت سلامت", callback_data="health_log")],
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
        ]),
        parse_mode='Markdown'
    )

async def enable_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable notification system"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Store user for notifications
    context.bot_data.setdefault('notification_users', set()).add(user_id)
    
    await query.edit_message_text(
        "🔔 **اعلان‌های هوشمند فعال شد!**\n\n"
        "از این پس شما اعلان‌های زیر را دریافت خواهید کرد:\n\n"
        "⏰ **اعلان‌های روزانه:**\n"
        "• یادآور دارو (ساعت ۸ صبح)\n"
        "• یادآور ثبت سلامت (ساعت ۸ شب)\n\n"
        "📅 **اعلان‌های هفتگی:**\n"
        "• یادآور اندازه‌گیری وزن (دوشنبه‌ها)\n"
        "• یادآور بررسی کلی (جمعه‌ها)\n\n"
        "🚨 **اعلان‌های فوری:**\n"
        "• یادآور واکسن (ماهانه)\n"
        "• هشدارهای سلامت\n\n"
        "💡 برای غیرفعال کردن، از منوی تنظیمات استفاده کنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 تست اعلان", callback_data="test_notification")],
            [InlineKeyboardButton("⚙️ تنظیمات اعلان", callback_data="notification_settings")],
            [InlineKeyboardButton("🔙 یادآورها", callback_data="reminders")]
        ])
    )
    
    # Send immediate test notification
    await send_test_notification(context, user_id)

async def test_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send test notification"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Send test notification after 3 seconds
    await query.edit_message_text(
        "📱 **تست اعلان**\n\n"
        "اعلان تست در ۳ ثانیه ارسال می‌شود...",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 یادآورها", callback_data="reminders")]
        ])
    )
    
    # Schedule test notification
    asyncio.create_task(send_delayed_test_notification(context, user_id))

async def send_test_notification(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Send immediate test notification"""
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="🔔 **اعلان تست**\n\n"
                 "✅ سیستم اعلان‌ها با موفقیت فعال شد!\n"
                 "از این پس یادآورهای مراقبت از حیوان خانگی‌تان را دریافت خواهید کرد.",
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Failed to send test notification: {e}")

async def send_delayed_test_notification(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Send delayed test notification"""
    await asyncio.sleep(3)
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="📱 **اعلان تست موفق!**\n\n"
                 "🎉 سیستم اعلان‌ها به درستی کار می‌کند.\n"
                 "یادآورهای روزانه شما فعال است.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 ثبت سلامت", callback_data="health_log")],
                [InlineKeyboardButton("⏰ یادآورها", callback_data="reminders")]
            ])
        )
    except Exception as e:
        print(f"Failed to send delayed notification: {e}")

async def notification_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Notification settings menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    notification_users = context.bot_data.get('notification_users', set())
    is_enabled = user_id in notification_users
    
    settings_text = "⚙️ **تنظیمات اعلان**\n\n"
    settings_text += f"وضعیت فعلی: {'🔔 فعال' if is_enabled else '🔕 غیرفعال'}\n\n"
    
    if is_enabled:
        settings_text += "📋 **اعلان‌های فعال:**\n"
        settings_text += "• یادآور دارو روزانه\n"
        settings_text += "• یادآور ثبت سلامت\n"
        settings_text += "• یادآورهای هفتگی\n"
        settings_text += "• هشدارهای فوری\n"
    else:
        settings_text += "❌ هیچ اعلانی فعال نیست.\n"
        settings_text += "برای دریافت یادآورهای مفید، اعلان‌ها را فعال کنید."
    
    keyboard = []
    if is_enabled:
        keyboard.append([InlineKeyboardButton("🔕 غیرفعال کردن", callback_data="disable_notifications")])
        keyboard.append([InlineKeyboardButton("📱 تست اعلان", callback_data="test_notification")])
    else:
        keyboard.append([InlineKeyboardButton("🔔 فعال کردن", callback_data="enable_notifications")])
    
    keyboard.append([InlineKeyboardButton("🔙 یادآورها", callback_data="reminders")])
    
    await query.edit_message_text(
        settings_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def disable_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Disable notifications"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    notification_users = context.bot_data.get('notification_users', set())
    notification_users.discard(user_id)
    
    await query.edit_message_text(
        "🔕 **اعلان‌ها غیرفعال شد**\n\n"
        "دیگر اعلان خودکار دریافت نخواهید کرد.\n\n"
        "💡 می‌توانید هر زمان از منوی یادآورها دوباره فعال کنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 فعال کردن مجدد", callback_data="enable_notifications")],
            [InlineKeyboardButton("🔙 یادآورها", callback_data="reminders")]
        ])
    )

async def medication_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show medication reminders with tracking"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pets = db.get_user_pets(user_id)
    
    # Check which pets need medication
    pets_with_meds = [pet for pet in pets if pet[11] and pet[11] != "ندارد"]
    
    if not pets_with_meds:
        await query.edit_message_text(
            "💊 **یادآور دارو**\n\n"
            "✅ هیچ‌کدام از حیوانات خانگی شما دارو مصرف نمی‌کنند.\n\n"
            "اگر دارویی تجویز شده، لطفاً در پروفایل حیوان خانگی ثبت کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🐾 ویرایش حیوانات", callback_data="my_pets")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="reminders")]
            ])
        )
        return
    
    med_text = "💊 **یادآور دارو**\n\n"
    
    for pet in pets_with_meds:
        pet_id = pet[0]
        last_med = db.get_last_task(pet_id, "medication")
        streak = db.get_task_streak(pet_id, "medication")
        
        med_text += f"🐾 **{pet[2]} ({pet[3]})**\n"
        med_text += f"💊 دارو: {pet[11]}\n"
        
        if last_med:
            hours_ago = get_hours_since(last_med)
            if hours_ago < 24:
                med_text += f"✅ آخرین دارو: {english_to_persian_numbers(str(int(hours_ago)))} ساعت پیش\n"
            else:
                days_ago = int(hours_ago / 24)
                med_text += f"⚠️ آخرین دارو: {english_to_persian_numbers(str(days_ago))} روز پیش\n"
        else:
            med_text += "❓ هنوز دارو ثبت نشده\n"
        
        if streak > 0:
            med_text += f"🔥 رکورد: {english_to_persian_numbers(str(streak))} روز\n"
        
        med_text += "---\n"
    
    med_text += "\n💡 **نکات مهم:**\n"
    med_text += "• دارو را در ساعت ثابت بدهید\n"
    med_text += "• دوز را کامل تکمیل کنید\n"
    
    # Create buttons for each pet
    keyboard = []
    for pet in pets_with_meds:
        pet_id = pet[0]
        keyboard.append([InlineKeyboardButton(f"✅ دارو {pet[2]} داده شد", callback_data=f"med_given_{pet_id}")])
    
    keyboard.extend([
        [InlineKeyboardButton("🔔 یادآور روزانه", callback_data="daily_med_reminder")],
        [InlineKeyboardButton("💬 سوال درباره دارو", callback_data="ai_chat")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="reminders")]
    ])
    
    await query.edit_message_text(
        med_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def daily_med_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set up daily medication reminder"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Add to daily reminder list
    context.bot_data.setdefault('daily_med_users', set()).add(user_id)
    
    await query.edit_message_text(
        "🔔 **یادآور روزانه دارو فعال شد!**\n\n"
        "⏰ هر روز ساعت ۸ صبح یادآور دارو دریافت خواهید کرد.\n\n"
        "📱 **نمونه پیام:**\n"
        "\"💊 وقت دارو! یادتان باشد دارو حیوان خانگی‌تان را بدهید.\"\n\n"
        "💡 برای غیرفعال کردن، از تنظیمات اعلان استفاده کنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 تست یادآور", callback_data="test_med_reminder")],
            [InlineKeyboardButton("🔙 یادآورها", callback_data="reminders")]
        ])
    )

async def test_med_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send test medication reminder"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pets = db.get_user_pets(user_id)
    pets_with_meds = [pet for pet in pets if pet[11] and pet[11] != "ندارد"]
    
    if pets_with_meds:
        # Send immediate medication reminder
        await send_medication_reminder(context, user_id, pets_with_meds)
        
        await query.edit_message_text(
            "📱 **یادآور تست ارسال شد!**\n\n"
            "✅ پیام یادآور دارو ارسال شد.\n"
            "این نوع پیام هر روز ساعت ۸ صبح دریافت خواهید کرد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 یادآورها", callback_data="reminders")]
            ])
        )

async def send_medication_reminder(context: ContextTypes.DEFAULT_TYPE, user_id: int, pets_with_meds):
    """Send medication reminder notification"""
    try:
        reminder_text = "💊 **یادآور دارو**\n\n"
        reminder_text += "⏰ وقت دارو رسیده!\n\n"
        
        for pet in pets_with_meds:
            reminder_text += f"🐾 {pet[2]}: {pet[11]}\n"
        
        reminder_text += "\n💡 بعد از دادن دارو، روی دکمه زیر کلیک کنید:"
        
        # Create quick action buttons
        keyboard = []
        for pet in pets_with_meds:
            pet_id = pet[0]
            keyboard.append([InlineKeyboardButton(f"✅ دارو {pet[2]} داده شد", callback_data=f"med_given_{pet_id}")])
        
        keyboard.append([InlineKeyboardButton("⏰ یادآورها", callback_data="reminders")])
        
        await context.bot.send_message(
            chat_id=user_id,
            text=reminder_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print(f"Failed to send medication reminder: {e}")

async def weekly_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show intelligent weekly schedule"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pets = db.get_user_pets(user_id)
    
    schedule_text = "📅 **برنامه هوشمند هفتگی**\n\n"
    
    # Get current day
    today = datetime.now().weekday()  # 0=Monday, 6=Sunday
    persian_days = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یکشنبه"]
    
    for i, day in enumerate(persian_days):
        is_today = (i == today)
        schedule_text += f"**{day}{'← امروز' if is_today else ''}:**\n"
        
        # Daily tasks
        schedule_text += "📊 ثبت سلامت\n"
        schedule_text += "💊 دارو (در صورت وجود)\n"
        schedule_text += "🍽️ غذا و آب تازه\n"
        
        # Weekly specific tasks
        if i == 0:  # Monday
            schedule_text += "⚖️ اندازه‌گیری وزن\n"
        elif i == 2:  # Wednesday  
            schedule_text += "🛁 حمام (در صورت نیاز)\n"
        elif i == 4:  # Friday
            schedule_text += "🏥 بررسی کلی سلامت\n"
        elif i == 6:  # Sunday
            schedule_text += "🎾 بازی و ورزش بیشتر\n"
        
        schedule_text += "---\n"
    
    # Show completion status for today
    today_tasks = get_today_task_status(pets)
    if today_tasks:
        schedule_text += "\n✅ **وضعیت امروز:**\n"
        for task in today_tasks:
            schedule_text += f"• {task}\n"
    
    await query.edit_message_text(
        schedule_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ کار امروز انجام شد", callback_data="daily_task_done")],
            [InlineKeyboardButton("🔔 یادآور هفتگی", callback_data="weekly_reminder")],
            [InlineKeyboardButton("📊 ثبت سلامت", callback_data="health_log")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="reminders")]
        ]),
        parse_mode='Markdown'
    )

async def weekly_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set up weekly reminders"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Add to weekly reminder list
    context.bot_data.setdefault('weekly_reminder_users', set()).add(user_id)
    
    await query.edit_message_text(
        "🔔 **یادآورهای هفتگی فعال شد!**\n\n"
        "📅 **برنامه اعلان‌ها:**\n"
        "• دوشنبه ۹ صبح: یادآور اندازه‌گیری وزن\n"
        "• چهارشنبه ۷ شب: یادآور حمام\n"
        "• جمعه ۸ شب: یادآور بررسی کلی\n"
        "• یکشنبه ۶ شب: یادآور بازی و ورزش\n\n"
        "💡 این یادآورها به شما کمک می‌کنند برنامه مراقبت منظم داشته باشید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 تست یادآور", callback_data="test_weekly_reminder")],
            [InlineKeyboardButton("🔙 یادآورها", callback_data="reminders")]
        ])
    )

async def med_given(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark medication as given for specific pet"""
    query = update.callback_query
    await query.answer()
    
    # Extract pet_id from callback data
    pet_id = int(query.data.split("_")[-1])
    
    # Log the medication task
    db.log_task(pet_id, "medication", "دارو داده شد")
    
    # Get pet info
    user_id = update.effective_user.id
    pets = db.get_user_pets(user_id)
    pet = next((p for p in pets if p[0] == pet_id), None)
    
    if pet:
        streak = db.get_task_streak(pet_id, "medication")
        
        await query.edit_message_text(
            f"✅ **دارو {pet[2]} داده شد**\n\n"
            f"عالی! دارو برای امروز ثبت شد.\n"
            f"🔥 رکورد شما: {english_to_persian_numbers(str(streak))} روز\n\n"
            "💡 نکته: اگر عوارض جانبی مشاهده کردید، با دامپزشک تماس بگیرید.",
            reply_markup=reminder_menu_buttons()
        )

async def daily_task_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark daily tasks as completed"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pets = db.get_user_pets(user_id)
    
    # Log daily care for all pets
    for pet in pets:
        db.log_task(pet[0], "daily_care", "مراقبت روزانه")
    
    total_streak = sum(db.get_task_streak(pet[0], "daily_care") for pet in pets)
    avg_streak = total_streak // len(pets) if pets else 0
    
    await query.edit_message_text(
        "✅ **مراقبت روزانه تکمیل شد**\n\n"
        f"🏆 شما مراقب فوق‌العاده‌ای هستید!\n"
        f"🔥 میانگین رکورد: {english_to_persian_numbers(str(avg_streak))} روز\n\n"
        "ادامه این روند باعث سلامت بهتر حیوانات خانگی‌تان می‌شود.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 ثبت سلامت", callback_data="health_log")],
            [InlineKeyboardButton("📅 برنامه فردا", callback_data="weekly_schedule")],
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
        ])
    )

# Background notification functions
async def send_daily_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Send daily reminders to all subscribed users"""
    notification_users = context.bot_data.get('notification_users', set())
    daily_med_users = context.bot_data.get('daily_med_users', set())
    
    for user_id in notification_users.union(daily_med_users):
        try:
            pets = db.get_user_pets(user_id)
            if pets:
                pets_with_meds = [pet for pet in pets if pet[11] and pet[11] != "ندارد"]
                if pets_with_meds:
                    await send_medication_reminder(context, user_id, pets_with_meds)
        except Exception as e:
            print(f"Failed to send daily reminder to {user_id}: {e}")

# Utility functions
def get_smart_reminders(pets):
    """Generate smart reminders based on real-time data"""
    reminders = []
    
    for pet in pets:
        pet_id = pet[0]
        pet_name = pet[2]
        
        # Check medication
        if pet[11] and pet[11] != "ندارد":
            last_med = db.get_last_task(pet_id, "medication")
            if not last_med or get_hours_since(last_med) > 20:  # More than 20 hours
                reminders.append(f"💊 دارو {pet_name}")
        
        # Check health logging
        health_logs = db.get_pet_health_logs(pet_id, 1)
        if not health_logs:
            reminders.append(f"📊 ثبت سلامت {pet_name}")
        else:
            last_log_date = health_logs[0][2]  # date field
            if get_days_since(last_log_date) > 1:
                reminders.append(f"📊 ثبت سلامت {pet_name}")
        
        # Check vaccine status
        if pet[12] in ["ناقص", "نمی‌دانم"]:
            reminders.append(f"💉 بررسی واکسن {pet_name}")
    
    return reminders

def get_care_streaks(pets):
    """Get care streaks for display"""
    streaks = []
    
    for pet in pets:
        pet_id = pet[0]
        pet_name = pet[2]
        
        # Medication streak
        if pet[11] and pet[11] != "ندارد":
            med_streak = db.get_task_streak(pet_id, "medication")
            if med_streak > 0:
                streaks.append(f"💊 {pet_name}: {english_to_persian_numbers(str(med_streak))} روز دارو")
        
        # Daily care streak
        care_streak = db.get_task_streak(pet_id, "daily_care")
        if care_streak > 0:
            streaks.append(f"🏆 {pet_name}: {english_to_persian_numbers(str(care_streak))} روز مراقبت")
    
    return streaks

def get_today_task_status(pets):
    """Get today's task completion status"""
    status = []
    
    for pet in pets:
        pet_id = pet[0]
        pet_name = pet[2]
        
        # Check if medication given today
        if pet[11] and pet[11] != "ندارد":
            last_med = db.get_last_task(pet_id, "medication")
            if last_med and get_hours_since(last_med) < 24:
                status.append(f"💊 {pet_name} - دارو داده شد")
        
        # Check if daily care done
        last_care = db.get_last_task(pet_id, "daily_care")
        if last_care and get_hours_since(last_care) < 24:
            status.append(f"🏆 {pet_name} - مراقبت انجام شد")
    
    return status

def get_hours_since(timestamp_str):
    """Calculate hours since timestamp"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now - timestamp
        return diff.total_seconds() / 3600
    except:
        return 999  # Very old

def get_days_since(date_str):
    """Calculate days since date"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        diff = today - date
        return diff.days
    except:
        return 999  # Very old

def get_months_since(timestamp_str):
    """Calculate months since timestamp"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now - timestamp
        return int(diff.days / 30)  # Approximate months
    except:
        return 999  # Very old

# Additional handlers for vaccine reminders
async def vaccine_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show vaccine reminders with time tracking"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pets = db.get_user_pets(user_id)
    
    vaccine_text = "💉 **یادآور واکسن**\n\n"
    
    urgent_pets = []
    normal_pets = []
    
    for pet in pets:
        pet_id = pet[0]
        vaccine_status = pet[12] or "نامشخص"
        created_date = pet[13]  # creation date
        
        # Calculate months since registration
        months_since = get_months_since(created_date)
        
        vaccine_text += f"🐾 **{pet[2]} ({pet[3]})**\n"
        vaccine_text += f"💉 وضعیت: {vaccine_status}\n"
        
        if vaccine_status == "ناقص":
            vaccine_text += "🔴 نیاز فوری به واکسن\n"
            urgent_pets.append(pet)
        elif vaccine_status == "نمی‌دانم":
            vaccine_text += "🟡 نیاز به بررسی\n"
            normal_pets.append(pet)
        elif months_since > 12:  # More than a year
            vaccine_text += "🟠 احتمال نیاز به تجدید\n"
            normal_pets.append(pet)
        else:
            vaccine_text += "✅ وضعیت مناسب\n"
        
        vaccine_text += f"📅 ثبت شده: {english_to_persian_numbers(str(months_since))} ماه پیش\n"
        vaccine_text += "---\n"
    
    vaccine_text += "\n📅 **برنامه واکسیناسیون:**\n"
    vaccine_text += "• سگ‌ها: سالانه (هاری، پاروو، لپتو)\n"
    vaccine_text += "• گربه‌ها: سالانه (پانلوکوپنی، کالیسی)\n"
    vaccine_text += "• سایر حیوانات: مشورت با دامپزشک\n"
    
    keyboard = []
    if urgent_pets:
        keyboard.append([InlineKeyboardButton("🚨 رزرو فوری واکسن", callback_data="urgent_vaccine")])
    
    keyboard.extend([
        [InlineKeyboardButton("📅 رزرو نوبت واکسن", callback_data="book_vaccine")],
        [InlineKeyboardButton("💬 سوال درباره واکسن", callback_data="ai_chat")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="reminders")]
    ])
    
    await query.edit_message_text(
        vaccine_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def book_vaccine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Book vaccine appointment"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📅 **رزرو نوبت واکسن**\n\n"
        "برای رزرو نوبت واکسیناسیون:\n\n"
        "📞 **تماس با کلینیک:**\n"
        "• کلینیک دامپزشکی محلی\n"
        "• بیمارستان دامپزشکی\n"
        "• دامپزشک خانگی\n\n"
        "📋 **مدارک لازم:**\n"
        "• کارت واکسیناسیون قبلی\n"
        "• شناسنامه حیوان خانگی\n"
        "• تاریخچه سلامت از ربات\n\n"
        "💡 **نکته:** قبل از واکسن، حیوان خانگی باید سالم باشد.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 بررسی سلامت", callback_data="health_analysis")],
            [InlineKeyboardButton("💬 سوال از دامپزشک", callback_data="ai_chat")],
            [InlineKeyboardButton("🔙 یادآورها", callback_data="reminders")]
        ])
    )

async def urgent_vaccine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Urgent vaccine reminder"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🚨 **رزرو فوری واکسن**\n\n"
        "⚠️ یک یا چند حیوان خانگی شما نیاز فوری به واکسن دارند.\n\n"
        "📞 **اقدام فوری:**\n"
        "• همین حالا با نزدیک‌ترین کلینیک تماس بگیرید\n"
        "• در صورت عدم دسترسی، با اورژانس دامپزشکی تماس بگیرید\n"
        "• تا زمان واکسن، از تماس با حیوانات دیگر جلوگیری کنید\n\n"
        "🔴 **خطر:** تأخیر در واکسیناسیون می‌تواند خطرناک باشد.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 راهنمای تماس", callback_data="emergency_contacts")],
            [InlineKeyboardButton("💬 مشاوره فوری", callback_data="ai_chat")],
            [InlineKeyboardButton("🔙 یادآورها", callback_data="reminders")]
        ])
    )
