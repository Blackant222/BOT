import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import config

# Import handlers
from handlers.pet_management import *
from handlers.health_tracking import *
from handlers.ai_chat import *
from handlers.health_analysis import *
from handlers.reminders import *
from handlers.subscription import *
from handlers.admin_analytics import *
from utils.analytics import analytics

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user = update.effective_user
    username = user.username or user.first_name
    
    # Add user to database
    from utils.database import db
    db.add_user(user.id, username)
    
    # Log user action
    analytics.log_user_action(user.id, username, "start_bot")
    
    welcome_text = f"""
🐾 **سلام {username}!**

به ربات مراقبت از حیوانات خانگی خوش آمدید!

🤖 **من چه کاری می‌توانم انجام دهم؟**
• ثبت اطلاعات حیوان خانگی شما
• پیگیری سلامت روزانه
• تحلیل هوشمند وضعیت سلامت
• مشاوره با دامپزشک هوشمند
• یادآورهای مراقبت

🚀 **برای شروع، یک حیوان خانگی اضافه کنید!**
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    help_text = """
🆘 **راهنمای استفاده**

📋 **دستورات اصلی:**
• /start - شروع مجدد ربات
• /help - نمایش این راهنما

🐾 **قابلیت‌های اصلی:**

**🐕 مدیریت حیوانات:**
• افزودن حیوان خانگی جدید
• مشاهده لیست حیوانات
• ویرایش اطلاعات

**📊 ثبت سلامت:**
• ثبت روزانه وزن، حالت، فعالیت
• پیگیری مدفوع و علائم
• یادداشت‌های سلامت

**🔍 تحلیل هوشمند:**
• نمره سلامت ۰-۱۰۰
• تشخیص مشکلات
• پیشنهادات بهبود

**💬 مشاوره AI:**
• پاسخ به سوالات
• راهنمایی فوری
• توصیه‌های تخصصی

**⏰ یادآورها:**
• یادآور دارو
• برنامه مراقبت
• اعلان‌های هوشمند

💡 **نکته:** همه قابلیت‌ها از منوی اصلی قابل دسترسی هستند.
    """
    
    await update.message.reply_text(
        help_text,
        reply_markup=main_menu_keyboard(),
        parse_mode='Markdown'
    )

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main menu handler"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🏠 **منوی اصلی**\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=main_menu_keyboard()
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    """Main function to run the bot"""
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Add pet management conversation handler
    pet_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_pet, pattern="^add_pet$")],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pet_name)],
            SPECIES: [CallbackQueryHandler(get_pet_species, pattern="^species_")],
            BREED: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pet_breed)],
            AGE_YEARS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pet_age_years)],
            AGE_MONTHS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pet_age_months)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pet_weight)],
            GENDER: [CallbackQueryHandler(get_pet_gender, pattern="^gender_")],
            NEUTERED: [CallbackQueryHandler(get_pet_neutered, pattern="^neutered_")],
            DISEASES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pet_diseases)],
            MEDICATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pet_medications)],
            VACCINES: [CallbackQueryHandler(get_pet_vaccines, pattern="^vaccine_")]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_add_pet, pattern="^back_main$"),
            CommandHandler("cancel", cancel_add_pet)
        ]
    )
    
    # Add health tracking conversation handler
    health_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_health_log, pattern="^health_log$")],
        states={
            SELECT_PET_HEALTH: [CallbackQueryHandler(select_pet_for_health, pattern="^select_pet_")],
            WEIGHT_LOG: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight_log)],
            MOOD_LOG: [CallbackQueryHandler(get_mood_log, pattern="^mood_")],
            STOOL_LOG: [CallbackQueryHandler(get_stool_log, pattern="^stool_")],
            APPETITE_LOG: [CallbackQueryHandler(get_appetite_log, pattern="^appetite_")],
            WATER_LOG: [CallbackQueryHandler(get_water_log, pattern="^water_")],
            TEMPERATURE_LOG: [CallbackQueryHandler(get_temperature_log, pattern="^temp_")],
            BREATHING_LOG: [CallbackQueryHandler(get_breathing_log, pattern="^breathing_")],
            ACTIVITY_LOG: [CallbackQueryHandler(get_activity_log, pattern="^activity_")],
            IMAGE_UPLOAD: [
                CallbackQueryHandler(handle_image_upload, pattern="^(upload_images|skip_images|upload_more)$"),
                CallbackQueryHandler(finish_image_upload, pattern="^finish_images$"),
                CallbackQueryHandler(categorize_image, pattern="^img_(blood_test|vet_note|pet_photo|delete)$"),
                MessageHandler(filters.PHOTO, process_uploaded_image),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_uploaded_image)
            ],
            NOTES_LOG: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_notes_log)]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_health_log, pattern="^back_main$"),
            CommandHandler("cancel", cancel_health_log)
        ]
    )
    
    # Add AI chat conversation handler with specialized modes
    ai_chat_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_ai_chat, pattern="^ai_chat$")],
        states={
            CHAT_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_message),
                CallbackQueryHandler(continue_chat, pattern="^continue_chat$"),
                CallbackQueryHandler(end_chat, pattern="^end_chat$"),
                CallbackQueryHandler(emergency_mode, pattern="^emergency_mode$"),
                CallbackQueryHandler(nutrition_mode, pattern="^nutrition_mode$"),
                CallbackQueryHandler(behavior_mode, pattern="^behavior_mode$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_chat, pattern="^back_main$"),
            CommandHandler("cancel", cancel_chat)
        ]
    )
    
    # Add conversation handlers
    application.add_handler(pet_conv_handler)
    application.add_handler(health_conv_handler)
    application.add_handler(ai_chat_handler)
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Admin analytics commands
    application.add_handler(CommandHandler("analytics", admin_analytics))
    application.add_handler(CommandHandler("detailed_analytics", admin_detailed_analytics))
    application.add_handler(CommandHandler("export_analytics", admin_export_data))
    application.add_handler(CommandHandler("get_analytics_file", admin_get_file))
    application.add_handler(CommandHandler("clear_analytics", admin_clear_analytics))
    
    # Add callback query handlers
    application.add_handler(CallbackQueryHandler(main_menu, pattern="^back_main$"))
    application.add_handler(CallbackQueryHandler(show_my_pets, pattern="^my_pets$"))
    application.add_handler(CallbackQueryHandler(show_pet_details, pattern="^select_pet_"))
    application.add_handler(CallbackQueryHandler(start_health_analysis, pattern="^health_analysis$"))
    application.add_handler(CallbackQueryHandler(analyze_pet_health, pattern="^analyze_health_"))
    application.add_handler(CallbackQueryHandler(show_pet_history, pattern="^history_"))
    
    # Skip button handlers
    application.add_handler(CallbackQueryHandler(handle_skip_breed, pattern="^skip_breed$"))
    application.add_handler(CallbackQueryHandler(handle_skip_weight, pattern="^skip_weight$"))
    application.add_handler(CallbackQueryHandler(handle_skip_notes, pattern="^skip_notes$"))
    application.add_handler(CallbackQueryHandler(handle_no_diseases, pattern="^no_diseases$"))
    application.add_handler(CallbackQueryHandler(handle_no_medications, pattern="^no_medications$"))
    
    # Pet detail action handlers
    application.add_handler(CallbackQueryHandler(add_health_data, pattern="^add_health_data_"))
    application.add_handler(CallbackQueryHandler(view_health_insights, pattern="^view_insights_"))
    application.add_handler(CallbackQueryHandler(edit_pet_info, pattern="^edit_pet_"))
    application.add_handler(CallbackQueryHandler(delete_pet, pattern="^delete_pet_"))
    application.add_handler(CallbackQueryHandler(pet_reminders, pattern="^pet_reminders_"))
    
    # Health tracking completion handlers
    application.add_handler(CallbackQueryHandler(finish_health_log, pattern="^finish_health_log$"))
    application.add_handler(CallbackQueryHandler(save_and_finish, pattern="^save_and_finish$"))
    
    # AI Chat enhanced handlers
    application.add_handler(CallbackQueryHandler(general_mode, pattern="^general_mode$"))
    application.add_handler(CallbackQueryHandler(health_insights, pattern="^health_insights$"))
    application.add_handler(CallbackQueryHandler(symptom_assessment, pattern="^symptom_assessment$"))
    application.add_handler(CallbackQueryHandler(predictive_timeline, pattern="^predictive_timeline$"))
    application.add_handler(CallbackQueryHandler(generate_insights, pattern="^generate_insights$"))
    application.add_handler(CallbackQueryHandler(generate_prediction, pattern="^generate_prediction$"))
    application.add_handler(CallbackQueryHandler(handle_ai_feedback, pattern="^feedback_"))
    application.add_handler(CallbackQueryHandler(handle_ai_feedback, pattern="^detailed_feedback_"))
    
    # Reminder handlers
    application.add_handler(CallbackQueryHandler(show_reminders, pattern="^reminders$"))
    application.add_handler(CallbackQueryHandler(enable_notifications, pattern="^enable_notifications$"))
    application.add_handler(CallbackQueryHandler(disable_notifications, pattern="^disable_notifications$"))
    application.add_handler(CallbackQueryHandler(test_notification, pattern="^test_notification$"))
    application.add_handler(CallbackQueryHandler(notification_settings, pattern="^notification_settings$"))
    application.add_handler(CallbackQueryHandler(medication_reminder, pattern="^medication_reminder$"))
    application.add_handler(CallbackQueryHandler(vaccine_reminder, pattern="^vaccine_reminder$"))
    application.add_handler(CallbackQueryHandler(weekly_schedule, pattern="^weekly_schedule$"))
    application.add_handler(CallbackQueryHandler(daily_med_reminder, pattern="^daily_med_reminder$"))
    application.add_handler(CallbackQueryHandler(test_med_reminder, pattern="^test_med_reminder$"))
    application.add_handler(CallbackQueryHandler(weekly_reminder, pattern="^weekly_reminder$"))
    application.add_handler(CallbackQueryHandler(med_given, pattern="^med_given_"))
    application.add_handler(CallbackQueryHandler(daily_task_done, pattern="^daily_task_done$"))
    application.add_handler(CallbackQueryHandler(book_vaccine, pattern="^book_vaccine$"))
    application.add_handler(CallbackQueryHandler(urgent_vaccine, pattern="^urgent_vaccine$"))
    
    # Subscription handlers
    application.add_handler(CallbackQueryHandler(show_subscription_status, pattern="^subscription_status$"))
    application.add_handler(CallbackQueryHandler(show_premium_upgrade, pattern="^upgrade_premium$"))
    application.add_handler(CallbackQueryHandler(start_free_trial, pattern="^free_trial$"))
    application.add_handler(CallbackQueryHandler(process_payment, pattern="^pay_(1month|3month|1year)$"))
    application.add_handler(CallbackQueryHandler(confirm_mock_payment, pattern="^confirm_payment_"))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("🤖 Pet Care Bot is starting...")
    print(f"📱 Bot token configured: {config.BOT_TOKEN[:10]}...")
    print(f"🗄️ Database path: {config.DATABASE_PATH}")
    print(f"🤖 OpenAI configured: {'Yes' if config.OPENAI_API_KEY else 'No'}")
    print("🚀 Bot is running! Press Ctrl+C to stop.")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
