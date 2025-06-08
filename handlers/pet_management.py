from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from utils.database import db
from utils.keyboards import *
from utils.persian_utils import *
from utils.analytics import analytics
from handlers.subscription import is_premium_feature_blocked, show_premium_blocked_feature
import config

# Conversation states
NAME, SPECIES, BREED, AGE_YEARS, AGE_MONTHS, WEIGHT, GENDER, NEUTERED, DISEASES, MEDICATIONS, VACCINES = range(11)

async def start_add_pet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start adding new pet"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check if user has premium for multiple pets
    if is_premium_feature_blocked(user_id, 'multiple_pets'):
        existing_pets = db.get_user_pets(user_id)
        if len(existing_pets) >= 1:
            await show_premium_blocked_feature(update, context, "افزودن حیوان خانگی دوم")
            return ConversationHandler.END
    
    # Initialize pet data
    context.user_data['pet_data'] = {}
    
    await query.edit_message_text(
        "🐕 افزودن حیوان خانگی جدید\n\n"
        "لطفاً نام حیوان خانگی خود را وارد کنید:",
        reply_markup=back_keyboard("back_main")
    )
    return NAME

async def get_pet_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get pet name"""
    name = clean_persian_input(update.message.text)
    
    if not validate_persian_name(name):
        await update.message.reply_text(
            "❌ نام وارد شده معتبر نیست. لطفاً نام فارسی معتبر وارد کنید:",
            reply_markup=back_keyboard("back_main")
        )
        return NAME
    
    context.user_data['pet_data']['name'] = name
    
    await update.message.reply_text(
        f"✅ نام: {name}\n\n"
        "حالا نوع حیوان خانگی را انتخاب کنید:",
        reply_markup=species_keyboard()
    )
    return SPECIES

async def get_pet_species(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get pet species"""
    query = update.callback_query
    await query.answer()
    
    species_map = {
        "species_dog": "سگ",
        "species_cat": "گربه", 
        "species_rabbit": "خرگوش",
        "species_bird": "پرنده",
        "species_hamster": "همستر"
    }
    
    if query.data in species_map:
        species = species_map[query.data]
        context.user_data['pet_data']['species'] = species
        
        await query.edit_message_text(
            f"✅ نوع: {species}\n\n"
            "نژاد حیوان خانگی را وارد کنید (اختیاری):",
            reply_markup=breed_input_keyboard()
        )
        return BREED
    
    return SPECIES

async def get_pet_breed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get pet breed"""
    if update.message:
        breed = clean_persian_input(update.message.text)
        if breed.lower() in ['رد', 'skip', 'نه']:
            breed = "نامشخص"
    else:
        breed = "نامشخص"
    
    context.user_data['pet_data']['breed'] = breed
    
    await update.message.reply_text(
        f"✅ نژاد: {breed}\n\n"
        "سن حیوان خانگی را به سال وارد کنید (عدد):\n"
        "مثال: ۲ یا 2",
        reply_markup=back_keyboard("back_species")
    )
    return AGE_YEARS

async def get_pet_age_years(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get pet age in years"""
    age_years = extract_number(update.message.text)
    
    if age_years is None or age_years < 0 or age_years > 30:
        await update.message.reply_text(
            "❌ سن وارد شده معتبر نیست. لطفاً عدد معتبر وارد کنید (۰ تا ۳۰):",
            reply_markup=back_keyboard("back_species")
        )
        return AGE_YEARS
    
    context.user_data['pet_data']['age_years'] = int(age_years)
    
    await update.message.reply_text(
        f"✅ سن: {english_to_persian_numbers(str(int(age_years)))} سال\n\n"
        "ماه‌های اضافی را وارد کنید (۰ تا ۱۱):\n"
        "مثال: ۶ یا 6",
        reply_markup=back_keyboard("back_species")
    )
    return AGE_MONTHS

async def get_pet_age_months(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get pet age in months"""
    age_months = extract_number(update.message.text)
    
    if age_months is None or age_months < 0 or age_months > 11:
        await update.message.reply_text(
            "❌ ماه وارد شده معتبر نیست. لطفاً عدد ۰ تا ۱۱ وارد کنید:",
            reply_markup=back_keyboard("back_species")
        )
        return AGE_MONTHS
    
    context.user_data['pet_data']['age_months'] = int(age_months)
    
    await update.message.reply_text(
        f"✅ سن کامل: {format_age(context.user_data['pet_data']['age_years'], int(age_months))}\n\n"
        "وزن حیوان خانگی را به کیلوگرم وارد کنید:\n"
        "مثال: ۵.۵ یا 5.5",
        reply_markup=back_keyboard("back_species")
    )
    return WEIGHT

async def get_pet_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get pet weight"""
    weight = extract_number(update.message.text)
    
    if weight is None or weight <= 0 or weight > 200:
        await update.message.reply_text(
            "❌ وزن وارد شده معتبر نیست. لطفاً عدد معتبر وارد کنید:",
            reply_markup=back_keyboard("back_species")
        )
        return WEIGHT
    
    context.user_data['pet_data']['weight'] = float(weight)
    
    await update.message.reply_text(
        f"✅ وزن: {format_weight(weight)}\n\n"
        "جنسیت حیوان خانگی را انتخاب کنید:",
        reply_markup=gender_keyboard()
    )
    return GENDER

async def get_pet_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get pet gender"""
    query = update.callback_query
    await query.answer()
    
    gender_map = {
        "gender_male": "نر",
        "gender_female": "ماده"
    }
    
    if query.data in gender_map:
        gender = gender_map[query.data]
        context.user_data['pet_data']['gender'] = gender
        
        await query.edit_message_text(
            f"✅ جنسیت: {gender}\n\n"
            "آیا حیوان خانگی شما عقیم شده است؟",
            reply_markup=yes_no_keyboard("neutered_yes", "neutered_no", "back_weight")
        )
        return NEUTERED
    
    return GENDER

async def get_pet_neutered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get neutering status"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "neutered_yes":
        is_neutered = True
        status_text = "بله"
    else:
        is_neutered = False
        status_text = "خیر"
    
    context.user_data['pet_data']['is_neutered'] = is_neutered
    
    await query.edit_message_text(
        f"✅ عقیم شده: {status_text}\n\n"
        "بیماری‌های قبلی یا فعلی را وارد کنید (اختیاری):",
        reply_markup=diseases_input_keyboard()
    )
    return DISEASES

async def get_pet_diseases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get pet diseases"""
    diseases = clean_persian_input(update.message.text)
    if diseases.lower() in ['ندارد', 'نه', 'خیر']:
        diseases = "ندارد"
    
    context.user_data['pet_data']['diseases'] = diseases
    
    await update.message.reply_text(
        f"✅ بیماری‌ها: {diseases}\n\n"
        "داروهای فعلی را وارد کنید (اختیاری):",
        reply_markup=medications_input_keyboard()
    )
    return MEDICATIONS

async def get_pet_medications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get pet medications"""
    medications = clean_persian_input(update.message.text)
    if medications.lower() in ['ندارد', 'نه', 'خیر']:
        medications = "ندارد"
    
    context.user_data['pet_data']['medications'] = medications
    
    print(f"🔍 DEBUG: Medications set, moving to VACCINES state")
    print(f"🔍 DEBUG: Current conversation state should be: {VACCINES}")
    
    await update.message.reply_text(
        f"✅ داروها: {medications}\n\n"
        "وضعیت واکسیناسیون را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ کامل", callback_data="vaccine_complete")],
            [InlineKeyboardButton("⚠️ ناقص", callback_data="vaccine_incomplete")],
            [InlineKeyboardButton("❓ نمی‌دانم", callback_data="vaccine_unknown")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_gender")]
        ])
    )
    return VACCINES

async def get_pet_vaccines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get vaccination status and save pet"""
    query = update.callback_query
    await query.answer()
    
    # Debug logging
    print(f"🔍 DEBUG: get_pet_vaccines called with callback_data: {query.data}")
    print(f"🔍 DEBUG: Current user_data: {context.user_data}")
    
    # Check if conversation data exists
    if 'pet_data' not in context.user_data:
        print("❌ DEBUG: No pet_data found in context - conversation was lost!")
        await query.edit_message_text(
            "❌ خطا: اطلاعات جلسه از دست رفته است.\n\n"
            "لطفاً مجدداً حیوان خانگی اضافه کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🐕 افزودن حیوان خانگی", callback_data="add_pet")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
            ])
        )
        return ConversationHandler.END
    
    vaccine_map = {
        "vaccine_complete": "کامل",
        "vaccine_incomplete": "ناقص", 
        "vaccine_unknown": "نمی‌دانم"
    }
    
    if query.data in vaccine_map:
        vaccine_status = vaccine_map[query.data]
        context.user_data['pet_data']['vaccine_status'] = vaccine_status
        
        print(f"✅ DEBUG: Vaccine status set to: {vaccine_status}")
        
        # Save pet to database
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        # Add user if not exists
        db.add_user(user_id, username)
        
        # Add pet
        pet_id = db.add_pet(user_id, context.user_data['pet_data'])
        
        # Log pet addition
        analytics.log_pet_action(user_id, username, "add_pet", {
            "pet_name": context.user_data['pet_data']['name'],
            "species": context.user_data['pet_data']['species'],
            "pet_id": pet_id
        })
        
        # Create summary
        pet_data = context.user_data['pet_data']
        summary = f"""
🎉 حیوان خانگی با موفقیت اضافه شد!

📋 خلاصه اطلاعات:
🐾 نام: {pet_data['name']}
🏷️ نوع: {pet_data['species']}
🧬 نژاد: {pet_data['breed']}
📅 سن: {format_age(pet_data['age_years'], pet_data['age_months'])}
⚖️ وزن: {format_weight(pet_data['weight'])}
♂️♀️ جنسیت: {pet_data['gender']}
✂️ عقیم شده: {'بله' if pet_data['is_neutered'] else 'خیر'}
🏥 بیماری‌ها: {pet_data['diseases']}
💊 داروها: {pet_data['medications']}
💉 واکسن: {vaccine_status}

شناسه حیوان: {english_to_persian_numbers(str(pet_id))}
        """
        
        await query.edit_message_text(
            summary,
            reply_markup=main_menu_keyboard()
        )
        
        # Clear conversation data
        context.user_data.clear()
        return ConversationHandler.END
    
    return VACCINES

async def cancel_add_pet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel adding pet"""
    context.user_data.clear()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "❌ افزودن حیوان خانگی لغو شد.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ افزودن حیوان خانگی لغو شد.",
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
            "🐾 شما هنوز حیوان خانگی اضافه نکرده‌اید.\n\n"
            "برای شروع، یک حیوان خانگی اضافه کنید!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🐕 افزودن حیوان خانگی", callback_data="add_pet")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
            ])
        )
        return
    
    await query.edit_message_text(
        "🐾 **حیوانات خانگی شما:**\n\n"
        "یکی را انتخاب کنید:",
        reply_markup=pets_list_keyboard(pets),
        parse_mode='Markdown'
    )

async def handle_skip_breed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle skip breed button"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['pet_data']['breed'] = "نامشخص"
    
    await query.edit_message_text(
        "✅ نژاد: نامشخص\n\n"
        "سن حیوان خانگی را به سال وارد کنید (عدد):\n"
        "مثال: ۲ یا 2",
        reply_markup=back_keyboard("back_species")
    )
    return AGE_YEARS

async def handle_skip_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle skip weight button"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['pet_data']['weight'] = 5.0  # Default weight
    
    await query.edit_message_text(
        "✅ وزن: پیش‌فرض (۵ کیلوگرم)\n\n"
        "جنسیت حیوان خانگی را انتخاب کنید:",
        reply_markup=gender_keyboard()
    )
    return GENDER

async def handle_skip_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle skip notes button"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['health_data']['notes'] = ""
    return await finish_health_log(update, context)

async def handle_no_diseases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle no diseases button"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['pet_data']['diseases'] = "ندارد"
    
    await query.edit_message_text(
        "✅ بیماری‌ها: ندارد\n\n"
        "داروهای فعلی را وارد کنید (اختیاری):",
        reply_markup=medications_input_keyboard()
    )
    return MEDICATIONS

async def handle_no_medications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle no medications button"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['pet_data']['medications'] = "ندارد"
    
    await query.edit_message_text(
        "✅ داروها: ندارد\n\n"
        "وضعیت واکسیناسیون را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ کامل", callback_data="vaccine_complete")],
            [InlineKeyboardButton("⚠️ ناقص", callback_data="vaccine_incomplete")],
            [InlineKeyboardButton("❓ نمی‌دانم", callback_data="vaccine_unknown")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_gender")]
        ])
    )
    return VACCINES

async def add_health_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add health data for specific pet"""
    query = update.callback_query
    await query.answer()
    
    # Extract pet_id from callback data
    pet_id = int(query.data.split("_")[-1])
    
    # Store pet_id in context for health logging
    context.user_data['selected_pet_id'] = pet_id
    
    # Redirect to health logging
    from handlers.health_tracking import start_health_log
    return await start_health_log(update, context)

async def view_health_insights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View health insights for specific pet"""
    query = update.callback_query
    await query.answer()
    
    # Extract pet_id from callback data
    pet_id = int(query.data.split("_")[-1])
    
    # Redirect to health analysis
    from handlers.health_analysis import analyze_pet_health
    # Modify callback data to match expected pattern
    query.data = f"analyze_health_{pet_id}"
    return await analyze_pet_health(update, context)

async def edit_pet_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit pet information"""
    query = update.callback_query
    await query.answer()
    
    # Extract pet_id from callback data
    pet_id = int(query.data.split("_")[-1])
    
    await query.edit_message_text(
        "✏️ **ویرایش اطلاعات حیوان**\n\n"
        "این قابلیت به زودی اضافه خواهد شد.\n"
        "در حال حاضر می‌توانید حیوان جدید اضافه کنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🐕 افزودن حیوان جدید", callback_data="add_pet")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"select_pet_{pet_id}")]
        ])
    )

async def delete_pet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete pet (premium feature)"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check premium access
    if is_premium_feature_blocked(user_id, 'delete_pets'):
        await show_premium_blocked_feature(update, context, "حذف حیوان خانگی")
        return
    
    # Extract pet_id from callback data
    pet_id = int(query.data.split("_")[-1])
    
    await query.edit_message_text(
        "⚠️ **حذف حیوان خانگی**\n\n"
        "این قابلیت به زودی اضافه خواهد شد.\n"
        "برای حذف، لطفاً با پشتیبانی تماس بگیرید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"select_pet_{pet_id}")]
        ])
    )

async def pet_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pet-specific reminders"""
    query = update.callback_query
    await query.answer()
    
    # Extract pet_id from callback data
    pet_id = int(query.data.split("_")[-1])
    
    user_id = update.effective_user.id
    pets = db.get_user_pets(user_id)
    pet = next((p for p in pets if p[0] == pet_id), None)
    
    if not pet:
        await query.edit_message_text(
            "❌ حیوان خانگی یافت نشد.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    reminder_text = f"⏰ **یادآورهای {pet[2]}**\n\n"
    
    # Check vaccination status
    if pet[12] in ['ناقص', 'نمی‌دانم']:
        reminder_text += "💉 **یادآور واکسیناسیون:**\n"
        reminder_text += "• لطفاً با دامپزشک مشورت کنید\n"
        reminder_text += "• واکسن‌های ضروری را تکمیل کنید\n\n"
    
    # Check medications
    if pet[11] and pet[11] != 'ندارد':
        reminder_text += "💊 **یادآور دارو:**\n"
        reminder_text += f"• داروهای فعلی: {pet[11]}\n"
        reminder_text += "• زمان مصرف را رعایت کنید\n\n"
    
    # General reminders
    reminder_text += "📋 **یادآورهای عمومی:**\n"
    reminder_text += "• ثبت روزانه سلامت\n"
    reminder_text += "• کنترل وزن هفتگی\n"
    reminder_text += "• بررسی حالت و رفتار\n"
    
    await query.edit_message_text(
        reminder_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏰ تنظیم یادآور", callback_data="reminders")],
            [InlineKeyboardButton("📊 ثبت سلامت", callback_data=f"add_health_data_{pet_id}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"select_pet_{pet_id}")]
        ]),
        parse_mode='Markdown'
    )

async def show_pet_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed pet information"""
    query = update.callback_query
    await query.answer()
    
    # Extract pet_id from callback data
    pet_id = int(query.data.split("_")[-1])
    
    user_id = update.effective_user.id
    pets = db.get_user_pets(user_id)
    pet = next((p for p in pets if p[0] == pet_id), None)
    
    if not pet:
        await query.edit_message_text(
            "❌ حیوان خانگی یافت نشد.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Format pet details
    pet_details = f"""
🐾 **{pet[2]}** ({pet[3]})

📋 **اطلاعات کامل:**
🧬 نژاد: {pet[4] or 'نامشخص'}
📅 سن: {format_age(pet[5], pet[6])}
⚖️ وزن: {format_weight(pet[7])}
♂️♀️ جنسیت: {pet[8]}
✂️ عقیم شده: {'بله' if pet[9] else 'خیر'}
🏥 بیماری‌ها: {pet[10] or 'ندارد'}
💊 داروها: {pet[11] or 'ندارد'}
💉 واکسن: {pet[12] or 'نامشخص'}

📅 تاریخ ثبت: {pet[13][:10] if pet[13] else 'نامشخص'}
🆔 شناسه: {english_to_persian_numbers(str(pet[0]))}
    """
    
    await query.edit_message_text(
        pet_details,
        reply_markup=pet_actions_keyboard(pet_id),
        parse_mode='Markdown'
    )

async def show_pet_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pet health history"""
    query = update.callback_query
    await query.answer()
    
    # Extract pet_id from callback data
    pet_id = int(query.data.split("_")[-1])
    
    user_id = update.effective_user.id
    pets = db.get_user_pets(user_id)
    pet = next((p for p in pets if p[0] == pet_id), None)
    
    if not pet:
        await query.edit_message_text(
            "❌ حیوان خانگی یافت نشد.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Get health logs
    health_logs = db.get_pet_health_logs(pet_id, 10)
    
    history_text = f"📋 **تاریخچه سلامت {pet[2]}**\n\n"
    
    if not health_logs:
        history_text += "❌ هنوز هیچ رکورد سلامتی ثبت نشده است.\n\n"
        history_text += "برای شروع، سلامت روزانه را ثبت کنید."
    else:
        history_text += f"📊 **آخرین {english_to_persian_numbers(str(len(health_logs)))} رکورد:**\n\n"
        
        for log in health_logs:
            date = log[2]  # date field
            weight = log[3]  # weight field
            mood = log[4]   # mood field
            activity = log[9]  # activity field
            
            history_text += f"📅 **{date}**\n"
            if weight:
                history_text += f"⚖️ وزن: {format_weight(weight)}\n"
            if mood:
                history_text += f"😊 حالت: {mood}\n"
            if activity:
                history_text += f"🏃 فعالیت: {activity}\n"
            history_text += "---\n"
    
    await query.edit_message_text(
        history_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 ثبت سلامت جدید", callback_data=f"log_health_{pet_id}")],
            [InlineKeyboardButton("📈 تحلیل سلامت", callback_data=f"analyze_health_{pet_id}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"select_pet_{pet_id}")]
        ]),
        parse_mode='Markdown'
    )
