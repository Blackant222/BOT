from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.openai_client import (
    get_ai_chat_response,
    get_specialized_consultation,
    analyze_health
)
from utils.prompt_manager import reload_prompts_command, get_prompt_status
from utils.openai_client import get_ai_health_insights
from utils.database import db
from utils.keyboards import *
from utils.persian_utils import *
from utils.analytics import analytics
from handlers.subscription import is_premium_feature_blocked, show_premium_blocked_feature, check_user_subscription
import config
import re
import json

# Chat states
CHAT_MESSAGE = range(1)

async def start_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Enhanced VETX - Advanced AI Veterinary Expert System"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pets = db.get_user_pets(user_id)
    
    pet_info = ""
    if pets:
        pet_info = f"\n\n🐾 **حیوانات ثبت شده شما:**\n"
        for pet in pets[:3]:  # Show first 3 pets
            pet_info += f"• {pet[2]} ({pet[3]}) - {format_age(pet[5], pet[6])}\n"
    
    await query.edit_message_text(
        f"🤖 **VETX 2.0 - سیستم دامپزشکی هوشمند پیشرفته**\n\n"
        f"سلام! من VETX نسخه جدید هستم با قابلیت‌های پیشرفته:\n\n"
        f"🧠 **مدل‌های هوش مصنوعی:**\n"
        f"• GPT-4.1 Nano برای مشاوره‌های عمومی\n"
        f"• O4-Mini Reasoning برای تحلیل‌های پیچیده\n"
        f"• سیستم بازخورد هوشمند\n"
        f"• تحلیل پیش‌بینانه سلامت\n\n"
        f"🎯 **حالت‌های تخصصی:**\n"
        f"• 🚨 اورژانس - تشخیص فوری خطرات\n"
        f"• 🥗 تغذیه - برنامه‌ریزی غذایی دقیق\n"
        f"• 🧠 رفتار - تحلیل رفتاری عمیق\n"
        f"• 📊 بینش سلامت - تحلیل پیش‌بینانه\n"
        f"• 🔍 ارزیابی علائم - تشخیص با کامل ترین داده‌ها\n"
        f"{pet_info}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🚨 اورژانس", callback_data="emergency_mode"),
                InlineKeyboardButton("🥗 تغذیه", callback_data="nutrition_mode")
            ],
            [
                InlineKeyboardButton("🧠 رفتار", callback_data="behavior_mode"),
                InlineKeyboardButton("💬 مشاوره عمومی", callback_data="general_mode")
            ],
            [
                InlineKeyboardButton("📊 بینش سلامت", callback_data="health_insights"),
                InlineKeyboardButton("🔍 ارزیابی علائم", callback_data="symptom_assessment")
            ],
            [
                InlineKeyboardButton("📡 پیش‌بینی سلامت", callback_data="predictive_timeline"),
                InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")
            ],
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main")]
        ]),
        parse_mode='Markdown'
    )
    return CHAT_MESSAGE

async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user chat message with enhanced AI routing"""
    chat_mode = context.user_data.get('chat_mode', 'general')
    
    if chat_mode in ['emergency', 'nutrition', 'behavior', 'general']:
        return await handle_enhanced_consultation(update, context)
    elif chat_mode == 'symptom_assessment':
        return await handle_symptom_assessment(update, context)
    elif chat_mode == 'health_insights':
        return await handle_health_insights_request(update, context)
    elif chat_mode == 'predictive_timeline':
        return await handle_predictive_timeline_request(update, context)
    else:
        return await handle_enhanced_consultation(update, context)

async def handle_enhanced_consultation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle enhanced AI consultation with new models and feedback"""
    user_message = clean_persian_input(update.message.text)
    user_id = update.effective_user.id
    
    if not user_message:
        await update.message.reply_text(
            "لطفاً سوال خود را به زبان فارسی بنویسید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
            ])
        )
        return CHAT_MESSAGE
    
    # Check premium limits
    if is_premium_feature_blocked(user_id, 'unlimited_ai_chat'):
        if check_daily_ai_limit(user_id):
            return await show_ai_limit_reached(update, context)
    
    # Get user's pets and health history
    pets = db.get_user_pets(user_id)
    pet_info = {}
    health_history = []
    
    if pets:
        # Use first pet as primary context
        primary_pet = pets[0]
        pet_info = {
            "id": primary_pet[0],
            "name": primary_pet[2],
            "species": primary_pet[3],
            "breed": primary_pet[4],
            "age_years": primary_pet[5],
            "age_months": primary_pet[6],
            "weight": primary_pet[7],
            "gender": primary_pet[8],
            "diseases": primary_pet[10] or "ندارد",
            "medications": primary_pet[11] or "ندارد",
            "vaccines": primary_pet[12] or "نامشخص"
        }
        
        # Get 30-day health history
        health_history = db.get_pet_health_logs(primary_pet[0], 30)
        health_history = [
            {
                "date": log[2],
                "weight": log[3],
                "mood": log[5],
                "appetite": log[6],
                "activity": log[9],
                "symptoms": log[10] or "ندارد",
                "notes": log[11] or ""
            }
            for log in health_history
        ]
    
    # Get consultation mode
    consultation_mode = context.user_data.get('chat_mode', 'general')
    
    # Show enhanced processing message
    processing_messages = {
        'emergency': "🚨 سیستم اورژانس در حال تحلیل فوری...",
        'nutrition': "🥗 متخصص تغذیه در حال محاسبه...",
        'behavior': "🧠 رفتارشناس هوشمند در حال تحلیل...",
        'general': "🤖 VETX در حال پردازش با GPT-4.1..."
    }
    
    processing_msg = await update.message.reply_text(
        processing_messages.get(consultation_mode, "🤖 VETX در حال پردازش...")
    )
    
    try:
        # Determine if user is premium
        is_premium = not is_premium_feature_blocked(user_id, 'unlimited_ai_chat')
        
        # Get enhanced AI consultation with new prompt system
        if consultation_mode == 'emergency':
            ai_response = await get_specialized_consultation(
                user_message, pet_info, 'emergency', is_premium,
                emergency_description=user_message,
                symptoms=user_message,
                duration="نامشخص"
            )
        else:
            ai_response = await get_ai_chat_response(
                user_message, pet_info, health_history, is_premium, ""
            )
        
        feedback_keyboard = None  # Will be implemented later
        
        # Log enhanced AI interaction
        username = update.effective_user.username or update.effective_user.first_name or "Unknown"
        is_premium = not is_premium_feature_blocked(user_id, 'unlimited_ai_chat')
        analytics.log_ai_chat(user_id, username, user_message, ai_response, is_premium)
        
        # ML DATA LOGGING - Log AI session for ML training
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        model_name = "gpt-4.1" if is_premium else "gpt-4.1-nano"
        
        if pet_info:  # Only log if we have pet context
            db.log_ai_session(
                user_id=user_id,
                pet_id=pet_info.get("id"),
                log_date=today,
                user_message=user_message,
                ai_response=ai_response,
                model_name=model_name,
                session_type=consultation_mode
            )
            
            # Extract AI insights for ML training
            risk_score = extract_risk_from_response(ai_response)
            tags = extract_tags_from_response(ai_response)
            summary = ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
            
            db.log_ai_insight(
                pet_id=pet_info.get("id"),
                log_date=today,
                ai_summary=summary,
                extracted_tags=tags,
                risk_score=risk_score,
                model_name=model_name
            )
        
        # Increment AI usage for free users
        if is_premium_feature_blocked(user_id, 'unlimited_ai_chat'):
            increment_ai_usage(user_id)
        
        # Delete processing message
        await processing_msg.delete()
        
        # Create enhanced response with mode-specific header
        response_headers = {
            'emergency': "🚨 **پاسخ اورژانس VETX:**",
            'nutrition': "🥗 **مشاوره تغذیه تخصصی:**",
            'behavior': "🧠 **تحلیل رفتاری پیشرفته:**",
            'general': "🩺 **مشاوره دامپزشکی VETX:**"
        }
        
        response_header = response_headers.get(consultation_mode, "🩺 **پاسخ VETX:**")
        
        # Enhanced navigation keyboard
        nav_keyboard = [
            [
                InlineKeyboardButton("🚨 اورژانس", callback_data="emergency_mode"),
                InlineKeyboardButton("🥗 تغذیه", callback_data="nutrition_mode")
            ],
            [
                InlineKeyboardButton("🧠 رفتار", callback_data="behavior_mode"),
                InlineKeyboardButton("📊 بینش سلامت", callback_data="health_insights")
            ],
            [
                InlineKeyboardButton("💬 سوال جدید", callback_data="continue_chat"),
                InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")
            ]
        ]
        
        # Send response with feedback system
        if feedback_keyboard:
            # Combine navigation and feedback keyboards
            combined_keyboard = nav_keyboard + feedback_keyboard.inline_keyboard
            reply_markup = InlineKeyboardMarkup(combined_keyboard)
        else:
            reply_markup = InlineKeyboardMarkup(nav_keyboard)
        
        await update.message.reply_text(
            f"{response_header}\n\n{ai_response}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await processing_msg.delete()
        await update.message.reply_text(
            f"❌ خطا در سیستم {get_mode_name(consultation_mode)}.\n"
            f"جزئیات خطا: {str(e)}\n"
            "لطفاً مجدداً تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="continue_chat")],
                [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
            ])
        )
    
    return CHAT_MESSAGE

async def handle_symptom_assessment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle enhanced symptom assessment with complete context"""
    user_message = clean_persian_input(update.message.text)
    user_id = update.effective_user.id
    
    # Get user's pets and complete health context
    pets = db.get_user_pets(user_id)
    if not pets:
        await update.message.reply_text(
            "⚠️ برای ارزیابی علائم، ابتدا حیوان خانگی خود را ثبت کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ ثبت حیوان", callback_data="add_pet")],
                [InlineKeyboardButton("❌ پایان", callback_data="end_chat")]
            ])
        )
        return CHAT_MESSAGE
    
    primary_pet = pets[0]
    pet_info = {
        "id": primary_pet[0],
        "name": primary_pet[2],
        "species": primary_pet[3],
        "breed": primary_pet[4],
        "age_years": primary_pet[5],
        "age_months": primary_pet[6],
        "weight": primary_pet[7],
        "diseases": primary_pet[10] or "ندارد",
        "medications": primary_pet[11] or "ندارد"
    }
    
    # Get comprehensive health history
    health_history = db.get_pet_health_logs(primary_pet[0], 30)
    health_history = [
        {
            "date": log[2],
            "weight": log[3],
            "mood": log[5],
            "appetite": log[6],
            "activity": log[9],
            "symptoms": log[10] or "ندارد",
            "notes": log[11] or ""
        }
        for log in health_history
    ]
    
    processing_msg = await update.message.reply_text(
        "🔍 سیستم ارزیابی علائم در حال تحلیل کامل داده‌ها..."
    )
    
    try:
        # Get enhanced symptom assessment using new system
        is_premium = not is_premium_feature_blocked(user_id, 'unlimited_ai_chat')
        assessment_response = await get_specialized_consultation(
            user_message, pet_info, 'general', is_premium,
            health_history=health_history,
            symptoms=user_message,
            symptom_duration="نامشخص",
            severity_level="متوسط"
        )
        feedback_keyboard = None
        
        await processing_msg.delete()
        
        # Enhanced response with urgency indicators
        response_text = f"🔍 **ارزیابی کامل علائم:**\n\n{assessment_response}"
        
        nav_keyboard = [
            [
                InlineKeyboardButton("🚨 اورژانس فوری", callback_data="emergency_mode"),
                InlineKeyboardButton("📊 بینش سلامت", callback_data="health_insights")
            ],
            [
                InlineKeyboardButton("🔍 علائم جدید", callback_data="symptom_assessment"),
                InlineKeyboardButton("❌ پایان", callback_data="end_chat")
            ]
        ]
        
        if feedback_keyboard:
            combined_keyboard = nav_keyboard + feedback_keyboard.inline_keyboard
            reply_markup = InlineKeyboardMarkup(combined_keyboard)
        else:
            reply_markup = InlineKeyboardMarkup(nav_keyboard)
        
        await update.message.reply_text(
            response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await processing_msg.delete()
        await update.message.reply_text(
            f"❌ خطا در ارزیابی علائم: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="symptom_assessment")],
                [InlineKeyboardButton("❌ پایان", callback_data="end_chat")]
            ])
        )
    
    return CHAT_MESSAGE

async def handle_health_insights_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle AI health insights generation"""
    user_id = update.effective_user.id
    
    # Get user's pets
    pets = db.get_user_pets(user_id)
    if not pets:
        await update.message.reply_text(
            "⚠️ برای تولید بینش سلامت، ابتدا حیوان خانگی خود را ثبت کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ ثبت حیوان", callback_data="add_pet")],
                [InlineKeyboardButton("❌ پایان", callback_data="end_chat")]
            ])
        )
        return CHAT_MESSAGE
    
    primary_pet = pets[0]
    pet_info = {
        "id": primary_pet[0],
        "name": primary_pet[2],
        "species": primary_pet[3],
        "breed": primary_pet[4],
        "age_years": primary_pet[5],
        "age_months": primary_pet[6],
        "weight": primary_pet[7],
        "diseases": primary_pet[10] or "ندارد",
        "medications": primary_pet[11] or "ندارد"
    }
    
    # Get comprehensive health history
    health_history = db.get_pet_health_logs(primary_pet[0], 30)
    health_history = [
        {
            "date": log[2],
            "weight": log[3],
            "mood": log[5],
            "appetite": log[6],
            "activity": log[9],
            "symptoms": log[10] or "ندارد",
            "notes": log[11] or ""
        }
        for log in health_history
    ]
    
    processing_msg = await update.message.reply_text(
        "📊 مدل O4-Mini Reasoning در حال تولید بینش‌های پیشرفته سلامت..."
    )
    
    try:
        # Generate AI health insights
        insights_response, feedback_keyboard = await get_ai_health_insights(
            pet_info, health_history, user_id
        )
        
        await processing_msg.delete()
        
        response_text = f"📊 **بینش‌های هوشمند سلامت:**\n\n{insights_response}"
        
        nav_keyboard = [
            [
                InlineKeyboardButton("📡 پیش‌بینی سلامت", callback_data="predictive_timeline"),
                InlineKeyboardButton("🔍 ارزیابی علائم", callback_data="symptom_assessment")
            ],
            [
                InlineKeyboardButton("🔄 بینش جدید", callback_data="health_insights"),
                InlineKeyboardButton("❌ پایان", callback_data="end_chat")
            ]
        ]
        
        if feedback_keyboard:
            combined_keyboard = nav_keyboard + feedback_keyboard.inline_keyboard
            reply_markup = InlineKeyboardMarkup(combined_keyboard)
        else:
            reply_markup = InlineKeyboardMarkup(nav_keyboard)
        
        await update.message.reply_text(
            response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await processing_msg.delete()
        await update.message.reply_text(
            f"❌ خطا در تولید بینش سلامت: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="health_insights")],
                [InlineKeyboardButton("❌ پایان", callback_data="end_chat")]
            ])
        )
    
    return CHAT_MESSAGE

async def handle_predictive_timeline_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle predictive timeline AI analysis"""
    user_id = update.effective_user.id
    
    # Get user's pets
    pets = db.get_user_pets(user_id)
    if not pets:
        await update.message.reply_text(
            "⚠️ برای پیش‌بینی سلامت، ابتدا حیوان خانگی خود را ثبت کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ ثبت حیوان", callback_data="add_pet")],
                [InlineKeyboardButton("❌ پایان", callback_data="end_chat")]
            ])
        )
        return CHAT_MESSAGE
    
    primary_pet = pets[0]
    pet_info = {
        "id": primary_pet[0],
        "name": primary_pet[2],
        "species": primary_pet[3],
        "breed": primary_pet[4],
        "age_years": primary_pet[5],
        "age_months": primary_pet[6],
        "weight": primary_pet[7],
        "diseases": primary_pet[10] or "ندارد",
        "medications": primary_pet[11] or "ندارد"
    }
    
    # Get comprehensive health history
    health_history = db.get_pet_health_logs(primary_pet[0], 30)
    health_history = [
        {
            "date": log[2],
            "weight": log[3],
            "mood": log[5],
            "appetite": log[6],
            "activity": log[9],
            "symptoms": log[10] or "ندارد",
            "notes": log[11] or ""
        }
        for log in health_history
    ]
    
    processing_msg = await update.message.reply_text(
        "📡 سیستم پیش‌بینی O4-Mini در حال تحلیل الگوهای سلامت..."
    )
    
    try:
        # Generate predictive timeline
        timeline_response, feedback_keyboard = await get_predictive_timeline(
            pet_info, health_history, user_id
        )
        
        await processing_msg.delete()
        
        response_text = f"📡 **پیش‌بینی سلامت و رادار خطر:**\n\n{timeline_response}"
        
        nav_keyboard = [
            [
                InlineKeyboardButton("📊 بینش سلامت", callback_data="health_insights"),
                InlineKeyboardButton("🚨 اورژانس", callback_data="emergency_mode")
            ],
            [
                InlineKeyboardButton("🔄 پیش‌بینی جدید", callback_data="predictive_timeline"),
                InlineKeyboardButton("❌ پایان", callback_data="end_chat")
            ]
        ]
        
        if feedback_keyboard:
            combined_keyboard = nav_keyboard + feedback_keyboard.inline_keyboard
            reply_markup = InlineKeyboardMarkup(combined_keyboard)
        else:
            reply_markup = InlineKeyboardMarkup(nav_keyboard)
        
        await update.message.reply_text(
            response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await processing_msg.delete()
        await update.message.reply_text(
            f"❌ خطا در پیش‌بینی سلامت: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="predictive_timeline")],
                [InlineKeyboardButton("❌ پایان", callback_data="end_chat")]
            ])
        )
    
    return CHAT_MESSAGE

# Mode handlers
async def emergency_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Emergency consultation mode with enhanced AI"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🚨 **حالت اورژانس VETX 2.0**\n\n"
        "⚡ **سیستم تشخیص فوری با GPT-4.1 Nano**\n\n"
        "لطفاً علائم و وضعیت فعلی حیوان خانگی‌تان را دقیق توضیح دهید:\n\n"
        "📋 **اطلاعات مورد نیاز:**\n"
        "• علائم مشاهده شده (دقیق)\n"
        "• زمان شروع علائم\n"
        "• شدت و تغییرات علائم\n"
        "• رفتار و حالت کلی حیوان\n"
        "• هر تغییر غیرعادی دیگر\n\n"
        "⚡ **مثال:** \"سگم ۲ ساعت پیش شروع به استفراغ خونی کرد، حالا بی‌حال است و نفس‌زنی دارد\"",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به چت", callback_data="continue_chat")],
            [InlineKeyboardButton("❌ پایان", callback_data="end_chat")]
        ]),
        parse_mode='Markdown'
    )
    
    context.user_data['chat_mode'] = 'emergency'
    return CHAT_MESSAGE

async def nutrition_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced nutrition consultation mode"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🥗 **مشاور تغذیه VETX 2.0**\n\n"
        "🧠 **متخصص تغذیه هوشمند با GPT-4.1**\n\n"
        "🎯 **خدمات تغذیه پیشرفته:**\n"
        "• محاسبه دقیق کالری روزانه\n"
        "• انتخاب غذای بهینه بر اساس سن/نژاد\n"
        "• برنامه‌ریزی وعده‌های غذایی\n"
        "• مکمل‌های غذایی تخصصی\n"
        "• رژیم‌های درمانی\n"
        "• حل مشکلات تغذیه‌ای\n\n"
        "💡 **مثال سوالات:**\n"
        "• \"چه مقدار غذا برای سگ ۱۰ کیلویی ۳ ساله مناسب است؟\"\n"
        "• \"گربه‌ام دیابت دارد، چه رژیمی بدهم؟\"\n"
        "• \"بهترین غذا برای توله سگ گلدن رتریور چیست؟\"",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به چت", callback_data="continue_chat")],
            [InlineKeyboardButton("❌ پایان", callback_data="end_chat")]
        ]),
        parse_mode='Markdown'
    )
    
    context.user_data['chat_mode'] = 'nutrition'
    return CHAT_MESSAGE

async def behavior_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced behavior analysis mode"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🧠 **متخصص رفتار VETX 2.0**\n\n"
        "🔬 **رفتارشناس هوشمند با تحلیل عمیق**\n\n"
        "🔍 **تحلیل رفتاری پیشرفته:**\n"
        "• شناسایی مشکلات رفتاری پیچیده\n"
        "• تحلیل اضطراب و استرس\n"
        "• برنامه آموزش و تربیت شخصی‌سازی شده\n"
        "• ارزیابی تغییرات رفتاری\n"
        "• حل رفتارهای تخریبی\n"
        "• بهبود روابط اجتماعی\n\n"
        "💭 **مثال سوالات:**\n"
        "• \"سگم شب‌ها مدام پارس می‌کند و همسایه‌ها شکایت دارند\"\n"
        "• \"گربه‌ام از وقتی نقل مکان کردیم، از لیتربکس استفاده نمی‌کند\"\n"
        "• \"حیوانم وقتی تنها می‌ماند، مبل‌ها را خراب می‌کند\"",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به چت", callback_data="continue_chat")],
            [InlineKeyboardButton("❌ پایان", callback_data="end_chat")]
        ]),
        parse_mode='Markdown'
    )
    
    context.user_data['chat_mode'] = 'behavior'
    return CHAT_MESSAGE

async def general_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """General consultation mode"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "💬 **مشاوره عمومی VETX 2.0**\n\n"
        "🩺 **دامپزشک عمومی هوشمند**\n\n"
        "سوال خود را در هر زمینه‌ای از مراقبت حیوانات بپرسید:\n\n"
        "🎯 **حوزه‌های تخصصی:**\n"
        "• سوالات کلی سلامت\n"
        "• مراقبت‌های پیشگیرانه\n"
        "• راهنمایی دارویی\n"
        "• برنامه واکسیناسیون\n"
        "• نکات نگهداری\n"
        "• مراقبت‌های نژاد-محور\n\n"
        "سوال خود را بپرسید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به چت", callback_data="continue_chat")],
            [InlineKeyboardButton("❌ پایان", callback_data="end_chat")]
        ]),
        parse_mode='Markdown'
    )
    
    context.user_data['chat_mode'] = 'general'
    return CHAT_MESSAGE

# New mode handlers
async def health_insights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Health insights mode"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📊 **بینش‌های هوشمند سلامت VETX 2.0**\n\n"
        "🧠 **تحلیل پیشرفته با مدل O4-Mini Reasoning**\n\n"
        "این سیستم تمام داده‌های سلامت حیوان شما را تحلیل می‌کند:\n\n"
        "🔍 **تحلیل‌های انجام شده:**\n"
        "• بررسی ۳۰ روز گذشته سلامت\n"
        "• شناسایی الگوهای پنهان\n"
        "• محاسبه ریسک‌های احتمالی\n"
        "• مقایسه با استانداردهای نژاد\n"
        "• تولید توصیه‌های عملی\n\n"
        "📈 **خروجی شامل:**\n"
        "• نمره کلی سلامت\n"
        "• روند تغییرات\n"
        "• هشدارهای مهم\n"
        "• پیشنهادات بهبود\n\n"
        "برای تولید بینش، روی دکمه زیر کلیک کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 تولید بینش", callback_data="generate_insights")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="continue_chat")],
            [InlineKeyboardButton("❌ پایان", callback_data="end_chat")]
        ]),
        parse_mode='Markdown'
    )
    
    context.user_data['chat_mode'] = 'health_insights'
    return CHAT_MESSAGE

async def symptom_assessment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Symptom assessment mode"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔍 **ارزیابی کامل علائم VETX 2.0**\n\n"
        "🧠 **سیستم تشخیص پیشرفته با کامل‌ترین داده‌ها**\n\n"
        "این سیستم علائم را با تمام اطلاعات حیوان شما تحلیل می‌کند:\n\n"
        "📋 **داده‌های مورد استفاده:**\n"
        "• پروفایل کامل حیوان\n"
        "• ۳۰ روز سابقه سلامت\n"
        "• روندهای اخیر\n"
        "• موارد مشابه قبلی\n"
        "• ویژگی‌های نژاد\n\n"
        "⚠️ **سطوح اورژانس:**\n"
        "🔴 اورژانس - مراجعه فوری\n"
        "🟠 فوری - ۲۴ ساعت\n"
        "🟡 متوسط - چند روز\n"
        "🟢 خفیف - نظارت\n\n"
        "لطفاً علائم مشاهده شده را دقیق توضیح دهید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="continue_chat")],
            [InlineKeyboardButton("❌ پایان", callback_data="end_chat")]
        ]),
        parse_mode='Markdown'
    )
    
    context.user_data['chat_mode'] = 'symptom_assessment'
    return CHAT_MESSAGE

async def predictive_timeline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Predictive timeline mode"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📡 **پیش‌بینی سلامت و رادار خطر VETX 2.0**\n\n"
        "🔮 **سیستم پیش‌بینی با مدل O4-Mini Reasoning**\n\n"
        "این سیستم آینده سلامت حیوان شما را پیش‌بینی می‌کند:\n\n"
        "📈 **تحلیل‌های زمانی:**\n"
        "• ۷ روز آینده - خطرات فوری\n"
        "• ۳۰ روز آینده - نگرانی‌های میان‌مدت\n"
        "• ۹۰ روز آینده - مسیر کلی سلامت\n\n"
        "🎯 **عوامل تحلیل:**\n"
        "• الگوهای ۳۰ روز گذشته\n"
        "• علائم هشدار زودهنگام\n"
        "• ریسک‌های نژادی\n"
        "• پیشرفت زمانی خطرات\n\n"
        "برای تولید پیش‌بینی، روی دکمه زیر کلیک کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 تولید پیش‌بینی", callback_data="generate_prediction")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="continue_chat")],
            [InlineKeyboardButton("❌ پایان", callback_data="end_chat")]
        ]),
        parse_mode='Markdown'
    )
    
    context.user_data['chat_mode'] = 'predictive_timeline'
    return CHAT_MESSAGE

# Callback handlers for new features
async def generate_insights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate health insights automatically"""
    query = update.callback_query
    await query.answer()
    
    # Trigger health insights generation
    context.user_data['chat_mode'] = 'health_insights'
    
    # Simulate a message to trigger the handler
    fake_message = type('obj', (object,), {
        'text': 'تولید بینش سلامت',
        'reply_text': query.message.reply_text
    })
    fake_update = type('obj', (object,), {
        'message': fake_message,
        'effective_user': update.effective_user
    })
    
    return await handle_health_insights_request(fake_update, context)

async def generate_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate predictive timeline automatically"""
    query = update.callback_query
    await query.answer()
    
    # Trigger predictive timeline generation
    context.user_data['chat_mode'] = 'predictive_timeline'
    
    # Simulate a message to trigger the handler
    fake_message = type('obj', (object,), {
        'text': 'تولید پیش‌بینی سلامت',
        'reply_text': query.message.reply_text
    })
    fake_update = type('obj', (object,), {
        'message': fake_message,
        'effective_user': update.effective_user
    })
    
    return await handle_predictive_timeline_request(fake_update, context)

# Feedback handling
async def handle_ai_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle AI feedback from users"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data.startswith("feedback_"):
        # Parse feedback data: feedback_{consultation_id}_{rating}
        parts = callback_data.split("_")
        consultation_id = parts[1]
        rating = int(parts[2])
        
        # Process feedback
        feedback_response = openai_client.feedback_collector.process_feedback(
            update.effective_user.id, consultation_id, rating
        )
        
        await query.edit_message_text(
            f"{query.message.text}\n\n✅ {feedback_response}",
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith("detailed_feedback_"):
        # Handle detailed feedback request
        consultation_id = callback_data.replace("detailed_feedback_", "")
        
        await query.edit_message_text(
            "📝 لطفاً بازخورد تفصیلی خود را بنویسید:\n\n"
            "• چه قسمت‌هایی مفید بود؟\n"
            "• چه بهبودهایی پیشنهاد می‌دهید؟\n"
            "• آیا پاسخ کامل بود؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ انصراف", callback_data="continue_chat")]
            ])
        )
        
        # Set context for detailed feedback
        context.user_data['awaiting_detailed_feedback'] = consultation_id

# Utility functions
async def continue_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Continue chat conversation"""
    query = update.callback_query
    await query.answer()
    
    # Clear any special modes
    if 'chat_mode' in context.user_data:
        context.user_data['chat_mode'] = 'general'
    
    await query.edit_message_text(
        "💬 **ادامه مشاوره**\n\n"
        "سوال بعدی خود را بپرسید یا یکی از حالت‌های تخصصی را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🚨 اورژانس", callback_data="emergency_mode"),
                InlineKeyboardButton("🥗 تغذیه", callback_data="nutrition_mode")
            ],
            [
                InlineKeyboardButton("🧠 رفتار", callback_data="behavior_mode"),
                InlineKeyboardButton("📊 بینش سلامت", callback_data="health_insights")
            ],
            [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
        ])
    )
    return CHAT_MESSAGE

async def end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """End AI chat"""
    query = update.callback_query
    await query.answer()
    
    # Clear all chat data
    context.user_data.clear()
    
    await query.edit_message_text(
        "✅ **چت با VETX 2.0 پایان یافت**\n\n"
        "🙏 متشکریم که از سیستم هوشمند دامپزشکی استفاده کردید!\n\n"
        "📊 **آمار این جلسه:**\n"
        "• مدل‌های AI پیشرفته استفاده شد\n"
        "• تحلیل کامل داده‌های سلامت\n"
        "• بازخورد برای بهبود سیستم\n\n"
        "⚠️ **یادآوری:** این مشاوره جایگزین ویزیت حضوری نیست.\n"
        "برای مشاوره‌های جدی لطفاً با دامپزشک واقعی مشورت کنید.",
        reply_markup=main_menu_keyboard(),
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def cancel_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel AI chat"""
    # Clear all chat data
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

# Helper functions
def get_mode_name(mode):
    """Get Persian name for chat mode"""
    mode_names = {
        'emergency': 'اورژانس',
        'nutrition': 'تغذیه',
        'behavior': 'رفتار',
        'general': 'عمومی',
        'health_insights': 'بینش سلامت',
        'symptom_assessment': 'ارزیابی علائم',
        'predictive_timeline': 'پیش‌بینی سلامت'
    }
    return mode_names.get(mode, 'عمومی')

async def show_ai_limit_reached(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show AI usage limit reached message"""
    usage_count = get_ai_usage_count(update.effective_user.id)
    limit_text = f"""
⚠️ **محدودیت چت روزانه**

شما امروز {usage_count} پیام AI استفاده کرده‌اید.
کاربران رایگان محدود به ۳ پیام در روز هستند.

🚀 **با ارتقاء به پریمیوم:**
• چت نامحدود با VETX 2.0
• دسترسی به تمام مدل‌های AI
• بینش‌های پیشرفته سلامت
• پیش‌بینی‌های زمانی
• مشاوره اورژانس ۲۴/۷

💰 **فقط ۵۹ هزار تومان/ماه**
    """
    
    keyboard = [
        [InlineKeyboardButton("🚀 ارتقاء به پریمیوم", callback_data="upgrade_premium")],
        [InlineKeyboardButton("🎁 ۷ روز رایگان", callback_data="free_trial")],
        [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
    ]
    
    await update.message.reply_text(
        limit_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return CHAT_MESSAGE

# Placeholder functions (to be implemented)
def check_daily_ai_limit(user_id):
    """Check if user has exceeded daily AI limit"""
    # This should check the actual usage from database
    return False  # Placeholder

def get_ai_usage_count(user_id):
    """Get current AI usage count for user"""
    # This should get actual count from database
    return 0  # Placeholder

def increment_ai_usage(user_id):
    """Increment AI usage count for user"""
    # This should increment in database
    pass  # Placeholder

# ML Helper Functions
def extract_risk_from_response(ai_response):
    """Extract risk score (0-10) from AI response for ML training"""
    try:
        # Look for risk indicators in Persian and English
        risk_keywords = {
            'اورژانس': 9, 'emergency': 9, 'فوری': 8, 'urgent': 8,
            'خطرناک': 7, 'dangerous': 7, 'نگران‌کننده': 6, 'concerning': 6,
            'متوسط': 5, 'moderate': 5, 'خفیف': 3, 'mild': 3,
            'عادی': 2, 'normal': 2, 'سالم': 1, 'healthy': 1
        }
        
        ai_lower = ai_response.lower()
        for keyword, score in risk_keywords.items():
            if keyword in ai_lower:
                return score
        
        # Default moderate risk if no keywords found
        return 5
    except:
        return 5

def extract_tags_from_response(ai_response):
    """Extract relevant tags from AI response for ML training"""
    try:
        # Common health tags in Persian and English
        tag_keywords = [
            'تغذیه', 'nutrition', 'وزن', 'weight', 'اشتها', 'appetite',
            'فعالیت', 'activity', 'خواب', 'sleep', 'استرس', 'stress',
            'درد', 'pain', 'تب', 'fever', 'استفراغ', 'vomiting',
            'اسهال', 'diarrhea', 'سرفه', 'cough', 'تنفس', 'breathing',
            'چشم', 'eye', 'گوش', 'ear', 'پوست', 'skin', 'مو', 'fur'
        ]
        
        found_tags = []
        ai_lower = ai_response.lower()
        
        for tag in tag_keywords:
            if tag in ai_lower:
                found_tags.append(tag)
        
        return ', '.join(found_tags[:5])  # Max 5 tags
    except:
        return "general"
