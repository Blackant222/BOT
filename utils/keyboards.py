from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    """Main menu keyboard with subscription status"""
    keyboard = [
        [InlineKeyboardButton("👤 وضعیت اشتراک", callback_data="subscription_status")],
        [InlineKeyboardButton("🐕 حیوانات من", callback_data="my_pets")],
        [InlineKeyboardButton("➕ افزودن حیوان", callback_data="add_pet")],
        [InlineKeyboardButton("📊 ثبت سلامت", callback_data="health_log")],
        [InlineKeyboardButton("🔍 تحلیل سلامت", callback_data="health_analysis")],
        [InlineKeyboardButton("🤖 مشاوره AI", callback_data="ai_chat")],
        [InlineKeyboardButton("⏰ یادآورها", callback_data="reminders")],
        [InlineKeyboardButton("💎 ارتقاء به پریمیوم", callback_data="upgrade_premium")]
    ]
    return InlineKeyboardMarkup(keyboard)

def species_keyboard():
    """Pet species selection"""
    keyboard = [
        [InlineKeyboardButton("🐕 سگ", callback_data="species_dog")],
        [InlineKeyboardButton("🐱 گربه", callback_data="species_cat")],
        [InlineKeyboardButton("🐰 خرگوش", callback_data="species_rabbit")],
        [InlineKeyboardButton("🐦 پرنده", callback_data="species_bird")],
        [InlineKeyboardButton("🐹 همستر", callback_data="species_hamster")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def gender_keyboard():
    """Pet gender selection"""
    keyboard = [
        [InlineKeyboardButton("♂️ نر", callback_data="gender_male")],
        [InlineKeyboardButton("♀️ ماده", callback_data="gender_female")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_species")]
    ]
    return InlineKeyboardMarkup(keyboard)

def yes_no_keyboard(yes_data, no_data, back_data=None):
    """Yes/No keyboard"""
    keyboard = [
        [InlineKeyboardButton("✅ بله", callback_data=yes_data)],
        [InlineKeyboardButton("❌ خیر", callback_data=no_data)]
    ]
    if back_data:
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=back_data)])
    return InlineKeyboardMarkup(keyboard)

def mood_keyboard():
    """Pet mood selection"""
    keyboard = [
        [InlineKeyboardButton("😊 شاد و پرانرژی", callback_data="mood_happy")],
        [InlineKeyboardButton("😐 عادی", callback_data="mood_normal")],
        [InlineKeyboardButton("😴 خسته و بی‌حال", callback_data="mood_tired")],
        [InlineKeyboardButton("😰 اضطراب", callback_data="mood_anxious")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_health")]
    ]
    return InlineKeyboardMarkup(keyboard)

def activity_keyboard():
    """Activity level selection"""
    keyboard = [
        [InlineKeyboardButton("🏃 زیاد", callback_data="activity_high")],
        [InlineKeyboardButton("🚶 متوسط", callback_data="activity_medium")],
        [InlineKeyboardButton("😴 کم", callback_data="activity_low")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_health")]
    ]
    return InlineKeyboardMarkup(keyboard)

def stool_keyboard():
    """Stool condition selection"""
    keyboard = [
        [InlineKeyboardButton("💩 طبیعی", callback_data="stool_normal")],
        [InlineKeyboardButton("💧 نرم", callback_data="stool_soft")],
        [InlineKeyboardButton("🪨 سفت", callback_data="stool_hard")],
        [InlineKeyboardButton("🩸 خونی", callback_data="stool_bloody")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_health")]
    ]
    return InlineKeyboardMarkup(keyboard)

def pets_list_keyboard(pets):
    """List of user's pets"""
    keyboard = []
    for pet in pets:
        pet_id, user_id, name, species, *_ = pet
        keyboard.append([InlineKeyboardButton(f"{species} {name}", callback_data=f"select_pet_{pet_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)

def pet_actions_keyboard(pet_id):
    """Actions for selected pet"""
    keyboard = [
        [InlineKeyboardButton("📊 ثبت سلامت", callback_data=f"add_health_data_{pet_id}")],
        [InlineKeyboardButton("🔍 مشاهده تحلیل", callback_data=f"view_insights_{pet_id}")],
        [InlineKeyboardButton("📈 تحلیل سلامت", callback_data=f"analyze_health_{pet_id}")],
        [InlineKeyboardButton("📋 تاریخچه", callback_data=f"history_{pet_id}")],
        [InlineKeyboardButton("⏰ یادآورها", callback_data=f"pet_reminders_{pet_id}")],
        [InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_pet_{pet_id}")],
        [InlineKeyboardButton("❌ حذف", callback_data=f"delete_pet_{pet_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="my_pets")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard(callback_data="back_main"):
    """Simple back button"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data=callback_data)]])

def reminder_menu_buttons():
    """Common reminder menu buttons"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 ثبت سلامت", callback_data="health_log")],
        [InlineKeyboardButton("💬 سوال از دامپزشک", callback_data="ai_chat")],
        [InlineKeyboardButton("🔙 یادآورها", callback_data="reminders")]
    ])

def task_completion_buttons(pet_id, task_type):
    """Task completion tracking buttons"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ انجام شد", callback_data=f"task_done_{pet_id}_{task_type}")],
        [InlineKeyboardButton("📊 ثبت سلامت", callback_data=f"log_health_{pet_id}")],
        [InlineKeyboardButton("🔙 یادآورها", callback_data="reminders")]
    ])

def appetite_keyboard():
    """Appetite level selection"""
    keyboard = [
        [InlineKeyboardButton("🍽️ زیاد", callback_data="appetite_high")],
        [InlineKeyboardButton("😋 نرمال", callback_data="appetite_normal")],
        [InlineKeyboardButton("😐 کم", callback_data="appetite_low")],
        [InlineKeyboardButton("❌ بدون اشتها", callback_data="appetite_none")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_health")]
    ]
    return InlineKeyboardMarkup(keyboard)

def water_keyboard():
    """Water intake selection"""
    keyboard = [
        [InlineKeyboardButton("💧 زیاد", callback_data="water_high")],
        [InlineKeyboardButton("💦 نرمال", callback_data="water_normal")],
        [InlineKeyboardButton("🥤 کم", callback_data="water_low")],
        [InlineKeyboardButton("❌ نمی‌نوشد", callback_data="water_none")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_health")]
    ]
    return InlineKeyboardMarkup(keyboard)

def temperature_keyboard():
    """Temperature selection"""
    keyboard = [
        [InlineKeyboardButton("🌡️ نرمال", callback_data="temp_normal")],
        [InlineKeyboardButton("🔥 داغ", callback_data="temp_hot")],
        [InlineKeyboardButton("🧊 سرد", callback_data="temp_cold")],
        [InlineKeyboardButton("🤒 تب", callback_data="temp_fever")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_health")]
    ]
    return InlineKeyboardMarkup(keyboard)

def breathing_keyboard():
    """Breathing status selection"""
    keyboard = [
        [InlineKeyboardButton("😮‍💨 نرمال", callback_data="breathing_normal")],
        [InlineKeyboardButton("💨 سریع", callback_data="breathing_fast")],
        [InlineKeyboardButton("🐌 آهسته", callback_data="breathing_slow")],
        [InlineKeyboardButton("😷 سرفه", callback_data="breathing_cough")],
        [InlineKeyboardButton("🔊 صدادار", callback_data="breathing_noisy")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_health")]
    ]
    return InlineKeyboardMarkup(keyboard)

def skip_keyboard(back_data="back_main"):
    """Skip button with back option"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_step")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=back_data)]
    ])

def breed_input_keyboard():
    """Keyboard for breed input with skip option"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_breed")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_species")]
    ])

def weight_input_keyboard():
    """Keyboard for weight input with skip option"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_weight")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ])

def notes_input_keyboard():
    """Keyboard for notes input with skip option"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ رد کردن", callback_data="skip_notes")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ])

def diseases_input_keyboard():
    """Keyboard for diseases input with skip option"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ ندارد", callback_data="no_diseases")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_gender")]
    ])

def medications_input_keyboard():
    """Keyboard for medications input with skip option"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ ندارد", callback_data="no_medications")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_gender")]
    ])
