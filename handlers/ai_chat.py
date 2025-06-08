from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.openai_client import get_ai_chat_response
from utils.database import db
from utils.keyboards import *
from utils.persian_utils import *
from utils.analytics import analytics
from handlers.subscription import is_premium_feature_blocked, show_premium_blocked_feature
import config

# Chat states
CHAT_MESSAGE = range(1)

async def start_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start simple AI chat"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check daily limit for free users
    if is_premium_feature_blocked(user_id, 'unlimited_ai_chat'):
        usage_count = db.get_ai_usage(user_id)
        if usage_count >= 3:
            await show_ai_limit_reached(update, context)
            return ConversationHandler.END
    
    # Get user's pets for context
    pets = db.get_user_pets(user_id)
    pet_info = ""
    if pets:
        pet_info = f"\n\n🐾 **حیوانات شما:**\n"
        for pet in pets[:3]:
            pet_info += f"• {pet[2]} ({pet[3]}) - {format_age(pet[5], pet[6])}\n"
    
    # Check if premium for pet selection
    is_premium = not is_premium_feature_blocked(user_id, 'unlimited_ai_chat')
    
    if is_premium and pets:
        # Premium users can select which pet to discuss
        keyboard = []
        for pet in pets:
            keyboard.append([InlineKeyboardButton(f"🐾 {pet[2]} ({pet[3]})", callback_data=f"chat_pet_{pet[0]}")])
        keyboard.append([InlineKeyboardButton("💬 سوال عمومی", callback_data="chat_general")])
        keyboard.append([InlineKeyboardButton("❌ انصراف", callback_data="back_main")])
        
        await query.edit_message_text(
            f"🤖 **مشاوره دامپزشک هوشمند**\n\n"
            f"💎 **کاربر پریمیوم** - چت نامحدود\n\n"
            f"درباره کدام حیوان می‌خواهید صحبت کنید؟{pet_info}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return CHAT_MESSAGE
    else:
        # Free users get simple chat
        usage_count = db.get_ai_usage(user_id) if not is_premium else 0
        remaining = max(0, 3 - usage_count) if not is_premium else "نامحدود"
        
        await query.edit_message_text(
            f"🤖 **مشاوره دامپزشک هوشمند**\n\n"
            f"💬 **چت ساده** - {remaining} پیام باقی‌مانده\n\n"
            f"سوال خود را بپرسید:{pet_info}\n\n"
            f"💡 **نکته:** پاسخ‌ها کلی هستند. برای مشاوره تخصصی با اطلاعات حیوان، پریمیوم شوید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 ارتقاء به پریمیوم", callback_data="upgrade_premium")],
                [InlineKeyboardButton("❌ انصراف", callback_data="back_main")]
            ]),
            parse_mode='Markdown'
        )
        context.user_data['selected_pet_id'] = None
        return CHAT_MESSAGE

async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user chat message (text or photo)"""
    user_id = update.effective_user.id
    
    # Handle photo messages
    if update.message.photo:
        await handle_chat_photo(update, context)
        return CHAT_MESSAGE
    
    # Handle text messages
    user_message = clean_persian_input(update.message.text) if update.message.text else ""
    
    if not user_message:
        await update.message.reply_text(
            "سوال خود را بنویسید یا عکس بفرستید! 📸",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
            ])
        )
        return CHAT_MESSAGE
    
    # Check premium status
    is_premium = not is_premium_feature_blocked(user_id, 'unlimited_ai_chat')
    
    # Check daily limit for free users
    if not is_premium:
        usage_count = db.get_ai_usage(user_id)
        if usage_count >= 3:
            await show_ai_limit_reached(update, context)
            return ConversationHandler.END
    
    # Get pet context if selected
    pet_info = {}
    health_history = []
    selected_pet_id = context.user_data.get('selected_pet_id')
    
    if is_premium and selected_pet_id:
        pets = db.get_user_pets(user_id)
        pet = next((p for p in pets if p[0] == selected_pet_id), None)
        if pet:
            pet_info = {
                "name": pet[2],
                "species": pet[3],
                "breed": pet[4],
                "age_years": pet[5],
                "age_months": pet[6],
                "weight": pet[7],
                "gender": pet[8],
                "diseases": pet[10] or "ندارد",
                "medications": pet[11] or "ندارد",
                "vaccines": pet[12] or "نامشخص"
            }
            
            # Get recent health history for premium users
            health_logs = db.get_pet_health_logs(selected_pet_id, 10)
            health_history = [
                {
                    "date": log[2],
                    "weight": log[3],
                    "mood": log[5],
                    "appetite": log[6],
                    "activity": log[9],
                    "notes": log[11] or ""
                }
                for log in health_logs
            ]
    
    # Show processing message
    processing_msg = await update.message.reply_text("🤖 در حال پردازش...")
    
    try:
        # Get conversation context
        conversation_context = context.user_data.get('conversation_history', [])
        
        # Add current message to context
        conversation_context.append(f"کاربر: {user_message}")
        
        # Keep only last 6 messages (3 exchanges)
        if len(conversation_context) > 6:
            conversation_context = conversation_context[-6:]
        
        # Format context for AI
        context_text = "\n".join(conversation_context[-4:]) if conversation_context else ""
        
        # Get AI response
        ai_response = await get_ai_chat_response(
            user_message, pet_info, health_history, is_premium, context_text
        )
        
        # Add AI response to context
        conversation_context.append(f"دامپزشک: {ai_response}")
        context.user_data['conversation_history'] = conversation_context
        
        # Log usage
        username = update.effective_user.username or update.effective_user.first_name
        analytics.log_ai_chat(user_id, username, user_message, ai_response, is_premium)
        
        # Increment usage for free users
        if not is_premium:
            db.increment_ai_usage(user_id)
            remaining = max(0, 3 - db.get_ai_usage(user_id))
        else:
            remaining = "نامحدود"
        
        # Delete processing message
        await processing_msg.delete()
        
        # Create response
        response_text = f"🩺 **پاسخ دامپزشک:**\n\n{ai_response}"
        
        if not is_premium:
            response_text += f"\n\n💬 **پیام‌های باقی‌مانده امروز:** {remaining}"
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("💬 سوال جدید", callback_data="continue_chat")],
            [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
        ]
        
        if not is_premium:
            keyboard.insert(0, [InlineKeyboardButton("🚀 ارتقاء به پریمیوم", callback_data="upgrade_premium")])
        
        await update.message.reply_text(
            response_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await processing_msg.delete()
        await update.message.reply_text(
            f"❌ خطا در پردازش: {str(e)}\n"
            "لطفاً مجدداً تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="continue_chat")],
                [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
            ])
        )
    
    return CHAT_MESSAGE

async def select_pet_for_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select pet for premium chat"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "chat_general":
        context.user_data['selected_pet_id'] = None
        pet_name = "عمومی"
    else:
        pet_id = int(query.data.split("_")[-1])
        context.user_data['selected_pet_id'] = pet_id
        
        # Get pet name
        user_id = update.effective_user.id
        pets = db.get_user_pets(user_id)
        pet = next((p for p in pets if p[0] == pet_id), None)
        pet_name = pet[2] if pet else "نامشخص"
    
    await query.edit_message_text(
        f"🤖 **مشاوره درباره {pet_name}**\n\n"
        f"💎 **کاربر پریمیوم** - چت نامحدود\n\n"
        f"سوال خود را درباره {pet_name} بپرسید:\n\n"
        f"💡 **مزایای پریمیوم:**\n"
        f"• دسترسی به اطلاعات کامل حیوان\n"
        f"• تحلیل تاریخچه سلامت\n"
        f"• پاسخ‌های تخصصی‌تر\n"
        f"• چت نامحدود",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 تغییر حیوان", callback_data="ai_chat")],
            [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
        ]),
        parse_mode='Markdown'
    )
    
    return CHAT_MESSAGE

async def continue_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Continue chat"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    is_premium = not is_premium_feature_blocked(user_id, 'unlimited_ai_chat')
    
    if not is_premium:
        usage_count = db.get_ai_usage(user_id)
        remaining = max(0, 3 - usage_count)
        if remaining == 0:
            await show_ai_limit_reached(update, context)
            return ConversationHandler.END
    
    await query.edit_message_text(
        "💬 **ادامه مشاوره**\n\n"
        "سوال بعدی خود را بپرسید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
        ])
    )
    return CHAT_MESSAGE

async def end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """End AI chat"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    await query.edit_message_text(
        "✅ **چت پایان یافت**\n\n"
        "متشکریم از استفاده شما!\n\n"
        "⚠️ **یادآوری:** این مشاوره جایگزین ویزیت دامپزشک نیست.",
        reply_markup=main_menu_keyboard(),
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def cancel_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel AI chat"""
    context.user_data.clear()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "❌ چت لغو شد.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ چت لغو شد.",
            reply_markup=main_menu_keyboard()
        )
    
    return ConversationHandler.END

async def handle_chat_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads in AI chat"""
    user_id = update.effective_user.id
    
    # Check premium status
    is_premium = not is_premium_feature_blocked(user_id, 'unlimited_ai_chat')
    
    # Check daily limit for free users
    if not is_premium:
        usage_count = db.get_ai_usage(user_id)
        if usage_count >= 3:
            await show_ai_limit_reached(update, context)
            return CHAT_MESSAGE
    
    # Show processing message
    processing_msg = await update.message.reply_text("📸 در حال تحلیل عکس...")
    
    try:
        # Get photo file
        photo = update.message.photo[-1]  # Get highest resolution
        photo_file = await photo.get_file()
        
        # Get pet context if selected
        pet_info = {}
        selected_pet_id = context.user_data.get('selected_pet_id')
        
        if is_premium and selected_pet_id:
            pets = db.get_user_pets(user_id)
            pet = next((p for p in pets if p[0] == selected_pet_id), None)
            if pet:
                pet_info = {
                    "name": pet[2],
                    "species": pet[3],
                    "breed": pet[4],
                    "age_years": pet[5],
                    "age_months": pet[6]
                }
        
        # Generate AI response for image
        if pet_info:
            ai_response = f"📸 عکس {pet_info['name']} رو دیدم!\n\n"
            ai_response += "چه چیز خاصی در این عکس نگرانتون کرده؟ 🤔\n\n"
            ai_response += "می‌تونید بگید:\n"
            ai_response += "• کدوم قسمت رو باید بررسی کنم؟\n"
            ai_response += "• چه علامتی دیدید؟\n"
            ai_response += "• چه مشکلی شک دارید؟"
        else:
            ai_response = "📸 عکس رو دیدم!\n\n"
            ai_response += "چه چیزی نگرانتون کرده؟ 🤔\n\n"
            ai_response += "لطفاً بگید:\n"
            ai_response += "• این عکس مربوط به چه حیوانیه؟\n"
            ai_response += "• چه علامت یا مشکلی دیدید؟\n"
            ai_response += "• چه سوالی دارید؟"
        
        # Log usage
        username = update.effective_user.username or update.effective_user.first_name
        analytics.log_ai_chat(user_id, username, "📸 عکس آپلود شد", ai_response, is_premium)
        
        # Increment usage for free users
        if not is_premium:
            db.increment_ai_usage(user_id)
            remaining = max(0, 3 - db.get_ai_usage(user_id))
        else:
            remaining = "نامحدود"
        
        # Delete processing message
        await processing_msg.delete()
        
        # Create response
        response_text = f"🩺 **پاسخ دامپزشک:**\n\n{ai_response}"
        
        if not is_premium:
            response_text += f"\n\n💬 **پیام‌های باقی‌مانده امروز:** {remaining}"
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("💬 سوال جدید", callback_data="continue_chat")],
            [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
        ]
        
        if not is_premium:
            keyboard.insert(0, [InlineKeyboardButton("🚀 ارتقاء به پریمیوم", callback_data="upgrade_premium")])
        
        await update.message.reply_text(
            response_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await processing_msg.delete()
        await update.message.reply_text(
            f"❌ خطا در پردازش عکس: {str(e)}\n"
            "لطفاً مجدداً تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="continue_chat")],
                [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
            ])
        )
    
    return CHAT_MESSAGE

async def show_ai_limit_reached(update, context):
    """Show AI limit reached message"""
    limit_text = """
⚠️ **محدودیت چت روزانه**

شما امروز ۳ پیام استفاده کرده‌اید.
کاربران رایگان محدود به ۳ پیام در روز هستند.

🚀 **با ارتقاء به پریمیوم:**
• چت نامحدود
• دسترسی به اطلاعات حیوانات
• تحلیل تاریخچه سلامت
• پاسخ‌های تخصصی‌تر

💰 **فقط ۵۹ هزار تومان/ماه**
    """
    
    keyboard = [
        [InlineKeyboardButton("🚀 ارتقاء به پریمیوم", callback_data="upgrade_premium")],
        [InlineKeyboardButton("🎁 ۷ روز رایگان", callback_data="free_trial")],
        [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            limit_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            limit_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
