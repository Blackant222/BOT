from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from utils.database import db
from utils.keyboards import *
from utils.persian_utils import *
from utils.analytics import analytics
from handlers.subscription import is_premium_feature_blocked, show_premium_blocked_feature
import config

# Health log states
SELECT_PET_HEALTH, WEIGHT_LOG, MOOD_LOG, STOOL_LOG, APPETITE_LOG, WATER_LOG, TEMPERATURE_LOG, BREATHING_LOG, ACTIVITY_LOG, NOTES_LOG, IMAGE_UPLOAD = range(11)

async def start_health_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start health logging"""
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
        return ConversationHandler.END
    
    await query.edit_message_text(
        "📊 ثبت سلامت روزانه\n\n"
        "برای کدام حیوان خانگی می‌خواهید سلامت ثبت کنید؟",
        reply_markup=pets_list_keyboard(pets)
    )
    return SELECT_PET_HEALTH

async def select_pet_for_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select pet for health logging"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("select_pet_"):
        pet_id = int(query.data.split("_")[-1])
        context.user_data['health_pet_id'] = pet_id
        context.user_data['health_data'] = {}
        
        # Get pet info
        user_id = update.effective_user.id
        pets = db.get_user_pets(user_id)
        selected_pet = next((pet for pet in pets if pet[0] == pet_id), None)
        
        if selected_pet:
            pet_name = selected_pet[2]
            await query.edit_message_text(
                f"📊 ثبت سلامت برای {pet_name}\n\n"
                "وزن فعلی را به کیلوگرم وارد کنید:\n"
                "مثال: ۵.۵ یا 5.5\n"
                "یا 'رد' برای رد کردن این مرحله",
                reply_markup=back_keyboard("back_main")
            )
            return WEIGHT_LOG
    
    return SELECT_PET_HEALTH

async def get_weight_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get weight for health log"""
    weight_text = clean_persian_input(update.message.text)
    
    if weight_text.lower() in ['رد', 'skip', 'نه']:
        weight = None
    else:
        weight = extract_number(weight_text)
        if weight is None or weight <= 0 or weight > 200:
            await update.message.reply_text(
                "❌ وزن وارد شده معتبر نیست. لطفاً عدد معتبر وارد کنید یا 'رد' بزنید:",
                reply_markup=back_keyboard("back_main")
            )
            return WEIGHT_LOG
    
    context.user_data['health_data']['weight'] = weight
    
    await update.message.reply_text(
        f"✅ وزن: {format_weight(weight) if weight else 'ثبت نشد'}\n\n"
        "حالت کلی حیوان خانگی را انتخاب کنید:",
        reply_markup=mood_keyboard()
    )
    return MOOD_LOG

async def get_mood_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get mood for health log"""
    query = update.callback_query
    await query.answer()
    
    mood_map = {
        "mood_happy": "شاد و پرانرژی",
        "mood_normal": "عادی",
        "mood_tired": "خسته و بی‌حال",
        "mood_anxious": "اضطراب"
    }
    
    if query.data in mood_map:
        mood = mood_map[query.data]
        context.user_data['health_data']['mood'] = mood
        
        await query.edit_message_text(
            f"✅ حالت: {mood}\n\n"
            "وضعیت مدفوع را انتخاب کنید:",
            reply_markup=stool_keyboard()
        )
        return STOOL_LOG
    
    return MOOD_LOG

async def get_stool_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get stool condition for health log"""
    query = update.callback_query
    await query.answer()
    
    stool_map = {
        "stool_normal": "طبیعی",
        "stool_soft": "نرم",
        "stool_hard": "سفت",
        "stool_bloody": "خونی"
    }
    
    if query.data in stool_map:
        stool = stool_map[query.data]
        context.user_data['health_data']['stool_info'] = stool
        
        await query.edit_message_text(
            f"✅ مدفوع: {stool}\n\n"
            "میزان اشتها را انتخاب کنید:",
            reply_markup=appetite_keyboard()
        )
        return APPETITE_LOG
    
    return STOOL_LOG

async def get_appetite_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get appetite level for health log"""
    query = update.callback_query
    await query.answer()
    
    appetite_map = {
        "appetite_high": "زیاد",
        "appetite_normal": "نرمال", 
        "appetite_low": "کم",
        "appetite_none": "بدون اشتها"
    }
    
    if query.data in appetite_map:
        appetite = appetite_map[query.data]
        context.user_data['health_data']['appetite'] = appetite
        
        await query.edit_message_text(
            f"✅ اشتها: {appetite}\n\n"
            "میزان نوشیدن آب را انتخاب کنید:",
            reply_markup=water_keyboard()
        )
        return WATER_LOG
    
    return APPETITE_LOG

async def get_water_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get water intake for health log"""
    query = update.callback_query
    await query.answer()
    
    water_map = {
        "water_high": "زیاد",
        "water_normal": "نرمال",
        "water_low": "کم",
        "water_none": "نمی‌نوشد"
    }
    
    if query.data in water_map:
        water = water_map[query.data]
        context.user_data['health_data']['water_intake'] = water
        
        await query.edit_message_text(
            f"✅ آب: {water}\n\n"
            "دمای بدن را انتخاب کنید:",
            reply_markup=temperature_keyboard()
        )
        return TEMPERATURE_LOG
    
    return WATER_LOG

async def get_temperature_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get temperature for health log"""
    query = update.callback_query
    await query.answer()
    
    temp_map = {
        "temp_normal": "نرمال",
        "temp_hot": "داغ",
        "temp_cold": "سرد",
        "temp_fever": "تب"
    }
    
    if query.data in temp_map:
        temperature = temp_map[query.data]
        context.user_data['health_data']['temperature'] = temperature
        
        await query.edit_message_text(
            f"✅ دما: {temperature}\n\n"
            "وضعیت تنفس را انتخاب کنید:",
            reply_markup=breathing_keyboard()
        )
        return BREATHING_LOG
    
    return TEMPERATURE_LOG

async def get_breathing_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get breathing status for health log"""
    query = update.callback_query
    await query.answer()
    
    breathing_map = {
        "breathing_normal": "نرمال",
        "breathing_fast": "سریع",
        "breathing_slow": "آهسته",
        "breathing_cough": "سرفه",
        "breathing_noisy": "صدادار"
    }
    
    if query.data in breathing_map:
        breathing = breathing_map[query.data]
        context.user_data['health_data']['breathing'] = breathing
        
        await query.edit_message_text(
            f"✅ تنفس: {breathing}\n\n"
            "سطح فعالیت حیوان خانگی را انتخاب کنید:",
            reply_markup=activity_keyboard()
        )
        return ACTIVITY_LOG
    
    return BREATHING_LOG

async def get_activity_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get activity level for health log"""
    query = update.callback_query
    await query.answer()
    
    activity_map = {
        "activity_high": "زیاد",
        "activity_medium": "متوسط",
        "activity_low": "کم"
    }
    
    if query.data in activity_map:
        activity = activity_map[query.data]
        context.user_data['health_data']['activity_level'] = activity
        
        await query.edit_message_text(
            f"✅ فعالیت: {activity}\n\n"
            "📸 آپلود تصاویر (اختیاری):\n\n"
            "می‌توانید تصاویر زیر را ارسال کنید:\n"
            "🩸 آزمایش خون\n"
            "📋 نسخه دامپزشک\n"
            "🐾 عکس حیوان خانگی\n\n"
            "یا 'رد' برای رد کردن و ادامه",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📸 آپلود تصاویر", callback_data="upload_images")],
                [InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_images")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
            ])
        )
        return IMAGE_UPLOAD
    
    return ACTIVITY_LOG

async def handle_image_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image upload decision"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "upload_images":
        user_id = update.effective_user.id
        
        # Check if user has premium for image uploads
        if is_premium_feature_blocked(user_id, 'image_upload'):
            await show_premium_blocked_feature(update, context, "آپلود تصاویر")
            return NOTES_LOG
        
        context.user_data['uploading_images'] = True
        context.user_data['uploaded_images'] = {}
        
        await query.edit_message_text(
            "📸 آپلود تصاویر\n\n"
            "لطفاً تصاویر خود را یکی یکی ارسال کنید:\n\n"
            "🩸 برای آزمایش خون: عکس ارسال کنید\n"
            "📋 برای نسخه دامپزشک: عکس ارسال کنید\n"
            "🐾 برای عکس حیوان: عکس ارسال کنید\n\n"
            "بعد از ارسال هر عکس، نوع آن را مشخص کنید.\n"
            "وقتی تمام شد 'تمام' بنویسید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ تمام شد", callback_data="finish_images")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
            ])
        )
        return IMAGE_UPLOAD
    
    elif query.data == "skip_images":
        await query.edit_message_text(
            "یادداشت اضافی درباره وضعیت حیوان خانگی (اختیاری):\n"
            "مثل: خوراک، خواب، علائم خاص و...\n"
            "یا 'رد' برای رد کردن",
            reply_markup=back_keyboard("back_main")
        )
        return NOTES_LOG
    
    return IMAGE_UPLOAD

async def process_uploaded_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process uploaded images"""
    if update.message and update.message.photo:
        # Get the largest photo
        photo = update.message.photo[-1]
        file_id = photo.file_id
        
        # Store temporarily
        if 'temp_image' not in context.user_data:
            context.user_data['temp_image'] = file_id
            
            await update.message.reply_text(
                "📸 عکس دریافت شد!\n\n"
                "این عکس چه نوعی است؟",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🩸 آزمایش خون", callback_data="img_blood_test")],
                    [InlineKeyboardButton("📋 نسخه دامپزشک", callback_data="img_vet_note")],
                    [InlineKeyboardButton("🐾 عکس حیوان", callback_data="img_pet_photo")],
                    [InlineKeyboardButton("❌ حذف", callback_data="img_delete")]
                ])
            )
            return IMAGE_UPLOAD
    
    elif update.message and update.message.text:
        text = update.message.text.lower()
        if text in ['تمام', 'finish', 'done']:
            return await finish_image_upload(update, context)
    
    return IMAGE_UPLOAD

async def categorize_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Categorize uploaded image"""
    query = update.callback_query
    await query.answer()
    
    if 'temp_image' not in context.user_data:
        await query.edit_message_text("❌ خطا: عکسی یافت نشد.")
        return IMAGE_UPLOAD
    
    file_id = context.user_data['temp_image']
    
    if query.data == "img_blood_test":
        context.user_data['health_data']['blood_test_image'] = file_id
        await query.edit_message_text("✅ آزمایش خون ذخیره شد!")
    
    elif query.data == "img_vet_note":
        context.user_data['health_data']['vet_note_image'] = file_id
        await query.edit_message_text("✅ نسخه دامپزشک ذخیره شد!")
    
    elif query.data == "img_pet_photo":
        context.user_data['health_data']['pet_image'] = file_id
        await query.edit_message_text("✅ عکس حیوان ذخیره شد!")
    
    elif query.data == "img_delete":
        await query.edit_message_text("❌ عکس حذف شد.")
    
    # Clear temp image
    del context.user_data['temp_image']
    
    # Ask for more images or finish
    await update.callback_query.message.reply_text(
        "می‌خواهید عکس دیگری اضافه کنید؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📸 عکس دیگر", callback_data="upload_more")],
            [InlineKeyboardButton("✅ تمام شد", callback_data="finish_images")]
        ])
    )
    return IMAGE_UPLOAD

async def finish_image_upload(update, context):
    """Finish image upload and go to notes"""
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "یادداشت اضافی درباره وضعیت حیوان خانگی (اختیاری):\n"
            "مثل: خوراک، خواب، علائم خاص و...\n"
            "یا 'رد' برای رد کردن",
            reply_markup=back_keyboard("back_main")
        )
    else:
        await update.message.reply_text(
            "یادداشت اضافی درباره وضعیت حیوان خانگی (اختیاری):\n"
            "مثل: خوراک، خواب، علائم خاص و...\n"
            "یا 'رد' برای رد کردن",
            reply_markup=back_keyboard("back_main")
        )
    return NOTES_LOG

async def get_notes_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get notes and save health log"""
    notes = clean_persian_input(update.message.text)
    
    if notes.lower() in ['رد', 'skip', 'نه']:
        notes = ""
    
    context.user_data['health_data']['notes'] = notes
    
    # Complete health data
    health_data = context.user_data['health_data']
    health_data.update({
        'food_type': 'عادی',  # Default values
        'symptoms': 'ندارد',
        'sleep_hours': 8,
        'medication_taken': True
    })
    
    # Save to database
    pet_id = context.user_data['health_pet_id']
    db.add_health_log(pet_id, health_data)
    
    # Log health action
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or "Unknown"
    analytics.log_health_action(user_id, username, "complete_health_log", {
        "pet_id": pet_id,
        "weight": health_data.get('weight'),
        "mood": health_data.get('mood'),
        "activity": health_data.get('activity_level')
    })
    
    # Create comprehensive summary
    summary = f"""
✅ سلامت با موفقیت ثبت شد!

📊 خلاصه ثبت امروز:
⚖️ وزن: {format_weight(health_data['weight']) if health_data['weight'] else 'ثبت نشد'}
😊 حالت: {health_data['mood']}
💩 مدفوع: {health_data['stool_info']}
🍽️ اشتها: {health_data.get('appetite', 'ثبت نشد')}
💧 آب: {health_data.get('water_intake', 'ثبت نشد')}
🌡️ دما: {health_data.get('temperature', 'ثبت نشد')}
😮‍💨 تنفس: {health_data.get('breathing', 'ثبت نشد')}
🏃 فعالیت: {health_data['activity_level']}
📝 یادداشت: {notes if notes else 'ندارد'}

تاریخ ثبت: امروز
    """
    
    await update.message.reply_text(
        summary,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📈 تحلیل سلامت", callback_data=f"analyze_health_{pet_id}")],
            [InlineKeyboardButton("📊 ثبت جدید", callback_data="health_log")],
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
        ])
    )
    
    # Clear conversation data
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_health_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel health logging"""
    context.user_data.clear()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "❌ ثبت سلامت لغو شد.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ ثبت سلامت لغو شد.",
            reply_markup=main_menu_keyboard()
        )
    
    return ConversationHandler.END

async def show_my_pets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's pets"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pets = db.get_user_pets(user_id)
    
    if not pets:
        await query.edit_message_text(
            "❌ شما هنوز حیوان خانگی اضافه نکرده‌اید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🐕 افزودن حیوان خانگی", callback_data="add_pet")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
            ])
        )
        return
    
    await query.edit_message_text(
        "🐾 حیوانات خانگی شما:\n\n"
        "برای مشاهده جزئیات و عملیات، روی نام کلیک کنید:",
        reply_markup=pets_list_keyboard(pets)
    )

async def show_pet_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pet details and actions"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("select_pet_"):
        pet_id = int(query.data.split("_")[-1])
        user_id = update.effective_user.id
        pets = db.get_user_pets(user_id)
        selected_pet = next((pet for pet in pets if pet[0] == pet_id), None)
        
        if selected_pet:
            pet_data = selected_pet
            pet_info = f"""
🐾 {pet_data[2]} ({pet_data[3]})

📋 اطلاعات کلی:
🧬 نژاد: {pet_data[4] or 'نامشخص'}
📅 سن: {format_age(pet_data[5], pet_data[6])}
⚖️ وزن: {format_weight(pet_data[7])}
♂️♀️ جنسیت: {pet_data[8]}
✂️ عقیم شده: {'بله' if pet_data[9] else 'خیر'}

🏥 وضعیت سلامت:
🦠 بیماری‌ها: {pet_data[10] or 'ندارد'}
💊 داروها: {pet_data[11] or 'ندارد'}
💉 واکسن: {pet_data[12] or 'نامشخص'}

شناسه: {english_to_persian_numbers(str(pet_id))}
            """
            
            await query.edit_message_text(
                pet_info,
                reply_markup=pet_actions_keyboard(pet_id)
            )

async def finish_health_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish health log without notes"""
    query = update.callback_query
    await query.answer()
    
    # Complete health data with defaults
    health_data = context.user_data.get('health_data', {})
    health_data.update({
        'notes': '',
        'food_type': 'عادی',
        'symptoms': 'ندارد',
        'sleep_hours': 8,
        'medication_taken': True
    })
    
    # Save to database
    pet_id = context.user_data.get('health_pet_id')
    if pet_id:
        db.add_health_log(pet_id, health_data)
        
        # Log health action
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Unknown"
        analytics.log_health_action(user_id, username, "complete_health_log", {
            "pet_id": pet_id,
            "weight": health_data.get('weight'),
            "mood": health_data.get('mood'),
            "activity": health_data.get('activity_level')
        })
        
        # Create summary
        summary = f"""
✅ سلامت با موفقیت ثبت شد!

📊 خلاصه ثبت امروز:
⚖️ وزن: {format_weight(health_data['weight']) if health_data.get('weight') else 'ثبت نشد'}
😊 حالت: {health_data.get('mood', 'ثبت نشد')}
💩 مدفوع: {health_data.get('stool_info', 'ثبت نشد')}
🍽️ اشتها: {health_data.get('appetite', 'ثبت نشد')}
💧 آب: {health_data.get('water_intake', 'ثبت نشد')}
🌡️ دما: {health_data.get('temperature', 'ثبت نشد')}
😮‍💨 تنفس: {health_data.get('breathing', 'ثبت نشد')}
🏃 فعالیت: {health_data.get('activity_level', 'ثبت نشد')}

تاریخ ثبت: امروز
        """
        
        await query.edit_message_text(
            summary,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📈 تحلیل سلامت", callback_data=f"analyze_health_{pet_id}")],
                [InlineKeyboardButton("📊 ثبت جدید", callback_data="health_log")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
            ])
        )
    else:
        await query.edit_message_text(
            "❌ خطا در ثبت سلامت.",
            reply_markup=main_menu_keyboard()
        )
    
    # Clear conversation data
    context.user_data.clear()
    return ConversationHandler.END

async def save_and_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save and finish health log"""
    query = update.callback_query
    await query.answer()
    
    return await finish_health_log(update, context)
