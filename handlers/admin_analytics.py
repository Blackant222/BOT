from telegram import Update
from telegram.ext import ContextTypes
from utils.analytics import analytics
from datetime import date, timedelta
import json
import os

# Admin user ID - @AshHTehrani
ADMIN_USER_ID = 691122097  # @AshHTehrani's user ID

async def admin_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show analytics dashboard for admin"""
    user_id = update.effective_user.id
    
    # Check if user is admin
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ شما دسترسی به این بخش ندارید.")
        return
    
    # Generate today's summary
    today_summary = analytics.generate_daily_summary()
    
    # Get function popularity
    popular_functions = analytics.get_function_popularity(7)
    
    # Create analytics report
    report = f"""
📊 **گزارش تحلیلی PetMagix**
📅 تاریخ: {today_summary['date']}

👥 **آمار کاربران امروز:**
• کل کاربران فعال: {today_summary['total_users']}
• کاربران پریمیوم: {today_summary['premium_users']}
• کل اقدامات: {today_summary['total_actions']}

💬 **فعالیت‌های امروز:**
• چت‌های AI: {today_summary['ai_chats']}
• اقدامات حیوان خانگی: {today_summary['pet_actions']}
• ثبت سلامت: {today_summary['health_actions']}
• اقدامات پریمیوم: {today_summary['premium_actions']}

🔥 **محبوب‌ترین عملکردها (۷ روز گذشته):**
"""
    
    for i, (func, count) in enumerate(list(popular_functions.items())[:10], 1):
        report += f"{i}. {func}: {count} بار\n"
    
    if today_summary['top_users']:
        report += f"\n👑 **فعال‌ترین کاربران امروز:**\n"
        for user_id, actions in today_summary['top_users'].items():
            report += f"• کاربر {user_id}: {actions} اقدام\n"
    
    await update.message.reply_text(report, parse_mode='Markdown')

async def admin_detailed_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed analytics for admin"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ شما دسترسی به این بخش ندارید.")
        return
    
    # Get analytics for last 7 days
    weekly_report = "📈 **گزارش هفتگی:**\n\n"
    
    total_users = set()
    total_actions = 0
    total_chats = 0
    
    for i in range(7):
        target_date = (date.today() - timedelta(days=i)).isoformat()
        summary = analytics.generate_daily_summary(target_date)
        
        weekly_report += f"📅 **{target_date}:**\n"
        weekly_report += f"• کاربران: {summary['total_users']}\n"
        weekly_report += f"• اقدامات: {summary['total_actions']}\n"
        weekly_report += f"• چت‌های AI: {summary['ai_chats']}\n"
        weekly_report += f"• پریمیوم: {summary['premium_users']}\n\n"
        
        total_actions += summary['total_actions']
        total_chats += summary['ai_chats']
    
    weekly_report += f"📊 **خلاصه هفته:**\n"
    weekly_report += f"• کل اقدامات: {total_actions}\n"
    weekly_report += f"• کل چت‌های AI: {total_chats}\n"
    weekly_report += f"• میانگین روزانه: {total_actions/7:.1f} اقدام\n"
    
    await update.message.reply_text(weekly_report, parse_mode='Markdown')

async def admin_export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export analytics data for admin"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ شما دسترسی به این بخش ندارید.")
        return
    
    today = date.today().isoformat()
    
    # List available analytics files
    analytics_files = []
    if os.path.exists("analytics"):
        for filename in os.listdir("analytics"):
            if filename.endswith('.json'):
                analytics_files.append(filename)
    
    if not analytics_files:
        await update.message.reply_text("📁 هیچ فایل تحلیلی یافت نشد.")
        return
    
    file_list = "📁 **فایل‌های تحلیلی موجود:**\n\n"
    for filename in sorted(analytics_files):
        file_size = os.path.getsize(f"analytics/{filename}")
        file_list += f"• {filename} ({file_size} bytes)\n"
    
    file_list += f"\n💡 برای دریافت فایل‌ها از دستور زیر استفاده کنید:\n"
    file_list += f"`/get_analytics_file filename.json`"
    
    await update.message.reply_text(file_list, parse_mode='Markdown')

async def admin_get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get specific analytics file"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ شما دسترسی به این بخش ندارید.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ نام فایل را مشخص کنید.\nمثال: `/get_analytics_file user_actions_2024-01-15.json`", parse_mode='Markdown')
        return
    
    filename = context.args[0]
    filepath = f"analytics/{filename}"
    
    if not os.path.exists(filepath):
        await update.message.reply_text(f"❌ فایل {filename} یافت نشد.")
        return
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # If file is too large, send summary instead
        if len(content) > 4000:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            summary = f"📄 **خلاصه {filename}:**\n"
            summary += f"• تعداد رکوردها: {len(data)}\n"
            summary += f"• حجم فایل: {len(content)} کاراکتر\n\n"
            summary += "🔗 فایل بزرگ است. برای دریافت کامل از ربات فایل درخواست کنید."
            
            await update.message.reply_text(summary, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"📄 **محتوای {filename}:**\n\n```json\n{content}\n```", parse_mode='Markdown')
    
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در خواندن فایل: {str(e)}")

async def admin_clear_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear old analytics data"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ شما دسترسی به این بخش ندارید.")
        return
    
    if not context.args or context.args[0] != "CONFIRM":
        await update.message.reply_text(
            "⚠️ **هشدار:** این عمل تمام داده‌های تحلیلی را پاک می‌کند.\n\n"
            "برای تأیید، دستور زیر را وارد کنید:\n"
            "`/clear_analytics CONFIRM`",
            parse_mode='Markdown'
        )
        return
    
    try:
        if os.path.exists("analytics"):
            import shutil
            shutil.rmtree("analytics")
            analytics.ensure_analytics_dir()
        
        await update.message.reply_text("✅ تمام داده‌های تحلیلی پاک شدند.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در پاک کردن داده‌ها: {str(e)}")
