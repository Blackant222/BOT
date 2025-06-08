from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.database import db
from utils.keyboards import *
from utils.persian_utils import *
from utils.openai_client import generate_diet_plan
from handlers.subscription import is_premium_feature_blocked, show_premium_blocked_feature
import config
from datetime import datetime

# Diet generator states
DIET_PET_SELECT, DIET_TYPE, DIET_GOALS, DIET_ALLERGIES, DIET_BUDGET, DIET_PREFERENCES = range(6)

async def start_diet_generator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start diet generator"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check if premium feature
    if is_premium_feature_blocked(user_id, 'diet_generator'):
        await show_premium_blocked_feature(update, context, "تولید برنامه غذایی")
        return ConversationHandler.END
    
    # Get user's pets
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
    
    # Initialize diet data
    context.user_data['diet_data'] = {}
    
    await query.edit_message_text(
        "🍽️ **تولید برنامه غذایی هوشمند**\n\n"
        "💎 **ویژه کاربران پریمیوم**\n\n"
        "برای کدام حیوان خانگی می‌خواهید برنامه غذایی تهیه کنم؟",
        reply_markup=pets_list_keyboard(pets),
        parse_mode='Markdown'
    )
    
    return DIET_PET_SELECT

async def select_pet_for_diet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select pet for diet plan"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("select_pet_"):
        pet_id = int(query.data.split("_")[-1])
        
        # Get pet info
        user_id = update.effective_user.id
        pets = db.get_user_pets(user_id)
        selected_pet = next((pet for pet in pets if pet[0] == pet_id), None)
        
        if not selected_pet:
            await query.edit_message_text(
                "❌ حیوان خانگی یافت نشد.",
                reply_markup=main_menu_keyboard()
            )
            return ConversationHandler.END
        
        context.user_data['diet_data']['pet_id'] = pet_id
        context.user_data['diet_data']['pet_info'] = selected_pet
        
        await query.edit_message_text(
            f"🍽️ **برنامه غذایی برای {selected_pet[2]}**\n\n"
            f"نوع برنامه غذایی مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🥗 رژیم کاهش وزن", callback_data="diet_weight_loss")],
                [InlineKeyboardButton("💪 رژیم افزایش وزن", callback_data="diet_weight_gain")],
                [InlineKeyboardButton("⚖️ حفظ وزن سالم", callback_data="diet_maintain")],
                [InlineKeyboardButton("🏥 رژیم درمانی", callback_data="diet_medical")],
                [InlineKeyboardButton("🐾 رژیم سنی", callback_data="diet_age_based")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
            ]),
            parse_mode='Markdown'
        )
        
        return DIET_TYPE
    
    return DIET_PET_SELECT

async def get_diet_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get diet type selection"""
    query = update.callback_query
    await query.answer()
    
    diet_types = {
        "diet_weight_loss": "کاهش وزن",
        "diet_weight_gain": "افزایش وزن", 
        "diet_maintain": "حفظ وزن",
        "diet_medical": "درمانی",
        "diet_age_based": "سنی"
    }
    
    if query.data in diet_types:
        diet_type = diet_types[query.data]
        context.user_data['diet_data']['diet_type'] = diet_type
        
        # Get specific goals based on diet type
        if query.data == "diet_weight_loss":
            goals_text = "چه مقدار کاهش وزن هدف دارید؟"
            goals_keyboard = [
                [InlineKeyboardButton("📉 کاهش ملایم (۵-۱۰%)", callback_data="goal_mild_loss")],
                [InlineKeyboardButton("📉 کاهش متوسط (۱۰-۲۰%)", callback_data="goal_moderate_loss")],
                [InlineKeyboardButton("📉 کاهش زیاد (بیش از ۲۰%)", callback_data="goal_major_loss")]
            ]
        elif query.data == "diet_weight_gain":
            goals_text = "چه مقدار افزایش وزن هدف دارید؟"
            goals_keyboard = [
                [InlineKeyboardButton("📈 افزایش ملایم (۵-۱۰%)", callback_data="goal_mild_gain")],
                [InlineKeyboardButton("📈 افزایش متوسط (۱۰-۲۰%)", callback_data="goal_moderate_gain")],
                [InlineKeyboardButton("📈 افزایش سریع (بیش از ۲۰%)", callback_data="goal_major_gain")]
            ]
        elif query.data == "diet_medical":
            goals_text = "کدام مشکل سلامتی را هدف قرار می‌دهیم؟"
            goals_keyboard = [
                [InlineKeyboardButton("🦴 مشکلات مفصلی", callback_data="goal_joint")],
                [InlineKeyboardButton("💔 مشکلات قلبی", callback_data="goal_heart")],
                [InlineKeyboardButton("🍃 مشکلات گوارشی", callback_data="goal_digestive")],
                [InlineKeyboardButton("🧠 مشکلات کلیوی", callback_data="goal_kidney")],
                [InlineKeyboardButton("🩸 دیابت", callback_data="goal_diabetes")]
            ]
        elif query.data == "diet_age_based":
            goals_text = "بر اساس سن، چه هدفی دارید؟"
            goals_keyboard = [
                [InlineKeyboardButton("🍼 تغذیه توله/بچه", callback_data="goal_puppy")],
                [InlineKeyboardButton("💪 تغذیه بالغ فعال", callback_data="goal_adult_active")],
                [InlineKeyboardButton("🧓 تغذیه سالمند", callback_data="goal_senior")]
            ]
        else:  # maintain
            goals_text = "چه هدف خاصی دارید؟"
            goals_keyboard = [
                [InlineKeyboardButton("💪 افزایش انرژی", callback_data="goal_energy")],
                [InlineKeyboardButton("✨ بهبود پوست و مو", callback_data="goal_coat")],
                [InlineKeyboardButton("🦴 تقویت استخوان", callback_data="goal_bone")],
                [InlineKeyboardButton("🧠 تقویت مغز", callback_data="goal_brain")]
            ]
        
        goals_keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_diet_type")])
        
        await query.edit_message_text(
            f"🎯 **هدف برنامه غذایی**\n\n"
            f"نوع انتخابی: {diet_type}\n\n"
            f"{goals_text}",
            reply_markup=InlineKeyboardMarkup(goals_keyboard),
            parse_mode='Markdown'
        )
        
        return DIET_GOALS
    
    return DIET_TYPE

async def get_diet_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get diet goals"""
    query = update.callback_query
    await query.answer()
    
    goals_map = {
        "goal_mild_loss": "کاهش وزن ملایم",
        "goal_moderate_loss": "کاهش وزن متوسط",
        "goal_major_loss": "کاهش وزن زیاد",
        "goal_mild_gain": "افزایش وزن ملایم",
        "goal_moderate_gain": "افزایش وزن متوسط", 
        "goal_major_gain": "افزایش وزن سریع",
        "goal_joint": "بهبود مشکلات مفصلی",
        "goal_heart": "بهبود سلامت قلب",
        "goal_digestive": "بهبود گوارش",
        "goal_kidney": "حمایت از کلیه",
        "goal_diabetes": "کنترل دیابت",
        "goal_puppy": "تغذیه رشد",
        "goal_adult_active": "تغذیه فعال",
        "goal_senior": "تغذیه سالمندی",
        "goal_energy": "افزایش انرژی",
        "goal_coat": "بهبود پوست و مو",
        "goal_bone": "تقویت استخوان",
        "goal_brain": "تقویت مغز"
    }
    
    if query.data in goals_map:
        goal = goals_map[query.data]
        context.user_data['diet_data']['goal'] = goal
        
        await query.edit_message_text(
            f"🚫 **آلرژی‌ها و محدودیت‌ها**\n\n"
            f"آیا حیوان خانگی شما آلرژی یا محدودیت غذایی خاصی دارد؟\n\n"
            f"مثال: آلرژی به مرغ، گوشت گاو، غلات، لبنیات و...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ دارد - می‌خواهم بنویسم", callback_data="has_allergies")],
                [InlineKeyboardButton("❌ ندارد", callback_data="no_allergies")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_diet_goals")]
            ]),
            parse_mode='Markdown'
        )
        
        return DIET_ALLERGIES
    
    return DIET_GOALS

async def handle_allergies_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle allergies selection"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "no_allergies":
        context.user_data['diet_data']['allergies'] = "ندارد"
        await ask_budget(query)
        return DIET_BUDGET
    elif query.data == "has_allergies":
        await query.edit_message_text(
            "🚫 **آلرژی‌ها و محدودیت‌ها**\n\n"
            "لطفاً آلرژی‌ها یا محدودیت‌های غذایی را بنویسید:\n\n"
            "مثال:\n"
            "• آلرژی به مرغ\n"
            "• حساسیت به غلات\n"
            "• مشکل با لبنیات\n"
            "• عدم تحمل گوشت گاو",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_diet_goals")]
            ]),
            parse_mode='Markdown'
        )
        return DIET_ALLERGIES
    
    return DIET_ALLERGIES

async def get_allergies_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get allergies text input"""
    allergies = clean_persian_input(update.message.text)
    context.user_data['diet_data']['allergies'] = allergies
    
    await update.message.reply_text(
        f"✅ آلرژی‌ها ثبت شد: {allergies}\n\n"
        "حالا به سوال بعدی می‌رویم..."
    )
    
    # Ask budget
    await ask_budget_message(update)
    return DIET_BUDGET

async def ask_budget(query):
    """Ask about budget"""
    await query.edit_message_text(
        "💰 **بودجه غذایی**\n\n"
        "بودجه ماهانه شما برای غذای حیوان خانگی چقدر است؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💵 اقتصادی (زیر ۵۰۰ هزار)", callback_data="budget_low")],
            [InlineKeyboardButton("💰 متوسط (۵۰۰ تا ۱ میلیون)", callback_data="budget_medium")],
            [InlineKeyboardButton("💎 بالا (بیش از ۱ میلیون)", callback_data="budget_high")],
            [InlineKeyboardButton("🤷 مهم نیست", callback_data="budget_no_limit")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_allergies")]
        ]),
        parse_mode='Markdown'
    )

async def ask_budget_message(update):
    """Ask about budget via message"""
    await update.message.reply_text(
        "💰 **بودجه غذایی**\n\n"
        "بودجه ماهانه شما برای غذای حیوان خانگی چقدر است؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💵 اقتصادی (زیر ۵۰۰ هزار)", callback_data="budget_low")],
            [InlineKeyboardButton("💰 متوسط (۵۰۰ تا ۱ میلیون)", callback_data="budget_medium")],
            [InlineKeyboardButton("💎 بالا (بیش از ۱ میلیون)", callback_data="budget_high")],
            [InlineKeyboardButton("🤷 مهم نیست", callback_data="budget_no_limit")]
        ]),
        parse_mode='Markdown'
    )

async def get_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get budget selection"""
    query = update.callback_query
    await query.answer()
    
    budget_map = {
        "budget_low": "اقتصادی",
        "budget_medium": "متوسط",
        "budget_high": "بالا",
        "budget_no_limit": "نامحدود"
    }
    
    if query.data in budget_map:
        budget = budget_map[query.data]
        context.user_data['diet_data']['budget'] = budget
        
        await query.edit_message_text(
            "🎯 **ترجیحات نهایی**\n\n"
            "ترجیح خاصی برای نوع غذا دارید؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🥫 غذای خشک", callback_data="pref_dry")],
                [InlineKeyboardButton("🍖 غذای مرطوب", callback_data="pref_wet")],
                [InlineKeyboardButton("🥗 ترکیبی", callback_data="pref_mixed")],
                [InlineKeyboardButton("🏠 غذای خانگی", callback_data="pref_homemade")],
                [InlineKeyboardButton("🌿 طبیعی/ارگانیک", callback_data="pref_organic")],
                [InlineKeyboardButton("🤷 مهم نیست", callback_data="pref_any")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_budget")]
            ]),
            parse_mode='Markdown'
        )
        
        return DIET_PREFERENCES
    
    return DIET_BUDGET

async def get_preferences_and_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get preferences and generate diet plan"""
    query = update.callback_query
    await query.answer()
    
    pref_map = {
        "pref_dry": "غذای خشک",
        "pref_wet": "غذای مرطوب",
        "pref_mixed": "ترکیبی",
        "pref_homemade": "خانگی",
        "pref_organic": "طبیعی/ارگانیک",
        "pref_any": "بدون ترجیح"
    }
    
    if query.data in pref_map:
        preference = pref_map[query.data]
        context.user_data['diet_data']['preference'] = preference
        
        # Show generating message
        await query.edit_message_text(
            "🤖 **در حال تولید برنامه غذایی...**\n\n"
            "🔍 تحلیل اطلاعات حیوان خانگی...\n"
            "📊 بررسی نیازهای تغذیه‌ای...\n"
            "🎯 طراحی برنامه مخصوص...\n"
            "📝 تهیه دستورالعمل‌ها...\n\n"
            "⏳ لطفاً صبر کنید...",
            parse_mode='Markdown'
        )
        
        # Generate diet plan
        await generate_and_show_diet_plan(query, context)
        return ConversationHandler.END
    
    return DIET_PREFERENCES

async def generate_and_show_diet_plan(query, context):
    """Generate and display the diet plan"""
    try:
        diet_data = context.user_data['diet_data']
        pet_info = diet_data['pet_info']
        
        # Get recent health data if available
        health_logs = db.get_pet_health_logs(diet_data['pet_id'], 5)
        
        # Prepare data for AI
        pet_details = {
            "name": pet_info[2],
            "species": pet_info[3],
            "breed": pet_info[4] or "نامشخص",
            "age_years": pet_info[5],
            "age_months": pet_info[6],
            "weight": pet_info[7],
            "gender": pet_info[8],
            "diseases": pet_info[10] or "ندارد",
            "medications": pet_info[11] or "ندارد"
        }
        
        # Generate diet plan using AI
        diet_plan = await generate_diet_plan(
            pet_details,
            diet_data['diet_type'],
            diet_data['goal'],
            diet_data['allergies'],
            diet_data['budget'],
            diet_data['preference'],
            health_logs
        )
        
        if not diet_plan or len(diet_plan.strip()) < 100:
            raise Exception("برنامه غذایی تولید نشد")
        
        # Format the response
        plan_text = f"""🍽️ **برنامه غذایی {pet_info[2]}**

📋 **خلاصه درخواست:**
• نوع برنامه: {diet_data['diet_type']}
• هدف: {diet_data['goal']}
• آلرژی‌ها: {diet_data['allergies']}
• بودجه: {diet_data['budget']}
• ترجیح: {diet_data['preference']}

🤖 **برنامه غذایی تولید شده:**

{diet_plan}

⚠️ **توجه مهم:**
• این برنامه بر اساس اطلاعات ارائه شده تهیه شده
• قبل از تغییر رژیم غذایی با دامپزشک مشورت کنید
• تغییرات را به تدریج اعمال کنید
• وزن و وضعیت حیوان را پیگیری کنید

📅 **تاریخ تولید:** {datetime.now().strftime('%Y-%m-%d')}
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 ثبت سلامت", callback_data="health_log")],
            [InlineKeyboardButton("💬 مشاوره AI", callback_data="ai_chat")],
            [InlineKeyboardButton("🔄 برنامه جدید", callback_data="diet_generator")],
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
        ]
        
        await query.edit_message_text(
            plan_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        # Save diet plan to database
        user_id = query.from_user.id
        plan_id = db.save_diet_plan(user_id, diet_data['pet_id'], diet_data, diet_plan)
        
        # Log the diet generation
        username = query.from_user.username or query.from_user.first_name
        from utils.analytics import analytics
        analytics.log_user_action(user_id, username, "diet_generated", {
            "pet_name": pet_info[2],
            "diet_type": diet_data['diet_type'],
            "goal": diet_data['goal'],
            "plan_id": plan_id
        })
        
        print(f"✅ Diet plan saved to database with ID: {plan_id}")
        
    except Exception as e:
        await query.edit_message_text(
            f"❌ **خطا در تولید برنامه غذایی**\n\n"
            f"متأسفانه نتوانستیم برنامه غذایی تولید کنیم.\n"
            f"خطا: {str(e)}\n\n"
            f"لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="diet_generator")],
                [InlineKeyboardButton("💬 مشاوره AI", callback_data="ai_chat")],
                [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
            ]),
            parse_mode='Markdown'
        )

async def cancel_diet_generator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel diet generator"""
    context.user_data.clear()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "❌ تولید برنامه غذایی لغو شد.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ تولید برنامه غذایی لغو شد.",
            reply_markup=main_menu_keyboard()
        )
    
    return ConversationHandler.END
