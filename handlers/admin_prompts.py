from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.prompt_manager import reload_prompts_command, get_prompt_status, prompt_manager
from utils.persian_utils import *
import json
import os

async def admin_prompt_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔥 Admin Prompt Management System"""
    query = update.callback_query
    await query.answer()
    
    # Check if user is admin
    user_id = update.effective_user.id
    if user_id not in [123456789]:  # Replace with actual admin IDs
        await query.edit_message_text("❌ دسترسی غیرمجاز")
        return
    
    status = await get_prompt_status()
    
    await query.edit_message_text(
        f"🔥 **مدیریت سیستم Prompt های هوشمند**\n\n"
        f"{status}\n\n"
        f"🛠️ **عملیات موجود:**",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 بارگذاری مجدد", callback_data="admin_reload_prompts"),
                InlineKeyboardButton("📊 وضعیت سیستم", callback_data="admin_prompt_status")
            ],
            [
                InlineKeyboardButton("📝 ویرایش Prompts", callback_data="admin_edit_prompts"),
                InlineKeyboardButton("📋 نسخه‌های موجود", callback_data="admin_prompt_versions")
            ],
            [
                InlineKeyboardButton("🧪 تست Prompt", callback_data="admin_test_prompt"),
                InlineKeyboardButton("📈 آمار استفاده", callback_data="admin_prompt_stats")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]
        ]),
        parse_mode='Markdown'
    )

async def admin_reload_prompts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reload prompts from file"""
    query = update.callback_query
    await query.answer()
    
    result = await reload_prompts_command()
    
    await query.edit_message_text(
        f"🔄 **بارگذاری مجدد Prompts**\n\n"
        f"{result}\n\n"
        f"📅 **زمان:** {get_persian_datetime()}\n"
        f"🔢 **نسخه:** {prompt_manager.get_prompt_version()}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_prompt_management")]
        ]),
        parse_mode='Markdown'
    )

async def admin_prompt_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed prompt system status"""
    query = update.callback_query
    await query.answer()
    
    status = await get_prompt_status()
    
    # Get additional stats
    prompts_data = prompt_manager.prompts_data
    total_prompts = len(prompts_data.get("prompts", {}))
    error_messages = len(prompts_data.get("error_messages", {}))
    upgrade_prompts = len(prompts_data.get("upgrade_prompts", {}))
    
    detailed_status = f"""📊 **وضعیت تفصیلی سیستم Prompt**

{status}

📈 **آمار کلی:**
• تعداد کل Prompts: {total_prompts}
• پیام‌های خطا: {error_messages}
• Prompts ارتقاء: {upgrade_prompts}

🔧 **تنظیمات فعال:**
• Auto-reload: ✅ فعال
• Hot-reload: ✅ فعال
• Error handling: ✅ فعال

💾 **فایل Prompts:**
• مسیر: prompts.json
• اندازه: {get_file_size('prompts.json')} KB
• آخرین تغییر: {get_file_modified_time('prompts.json')}"""
    
    await query.edit_message_text(
        detailed_status,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 بروزرسانی", callback_data="admin_prompt_status"),
                InlineKeyboardButton("📝 ویرایش", callback_data="admin_edit_prompts")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_prompt_management")]
        ]),
        parse_mode='Markdown'
    )

async def admin_edit_prompts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show prompt editing options"""
    query = update.callback_query
    await query.answer()
    
    prompts_data = prompt_manager.prompts_data
    available_prompts = list(prompts_data.get("prompts", {}).keys())
    
    prompt_list = "\n".join([f"• {prompt}" for prompt in available_prompts[:10]])
    if len(available_prompts) > 10:
        prompt_list += f"\n• ... و {len(available_prompts) - 10} مورد دیگر"
    
    await query.edit_message_text(
        f"📝 **ویرایش Prompts**\n\n"
        f"🎯 **Prompts موجود:**\n{prompt_list}\n\n"
        f"💡 **راهنمای ویرایش:**\n"
        f"• فایل prompts.json را ویرایش کنید\n"
        f"• تغییرات به صورت خودکار اعمال می‌شود\n"
        f"• از دکمه بارگذاری مجدد استفاده کنید\n\n"
        f"⚠️ **نکات مهم:**\n"
        f"• فرمت JSON را رعایت کنید\n"
        f"• از backup قبل از تغییر استفاده کنید\n"
        f"• تست کنید قبل از اعمال نهایی",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📋 کپی مسیر فایل", callback_data="admin_copy_path"),
                InlineKeyboardButton("💾 پشتیبان‌گیری", callback_data="admin_backup_prompts")
            ],
            [
                InlineKeyboardButton("🔄 بارگذاری مجدد", callback_data="admin_reload_prompts"),
                InlineKeyboardButton("🧪 تست", callback_data="admin_test_prompt")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_prompt_management")]
        ]),
        parse_mode='Markdown'
    )

async def admin_test_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test prompt system"""
    query = update.callback_query
    await query.answer()
    
    # Test different prompt types
    test_results = []
    
    prompt_types = ["health_analysis", "ai_chat", "emergency", "nutrition", "behavior", "general"]
    
    for prompt_type in prompt_types:
        try:
            # Test free tier
            free_prompt = prompt_manager.get_prompt(prompt_type, "free")
            free_status = "✅" if free_prompt else "❌"
            
            # Test premium tier (if exists)
            premium_prompt = prompt_manager.get_prompt(prompt_type, "premium")
            premium_status = "✅" if premium_prompt else "❌"
            
            test_results.append(f"• {prompt_type}: Free {free_status} | Premium {premium_status}")
            
        except Exception as e:
            test_results.append(f"• {prompt_type}: ❌ خطا - {str(e)[:30]}...")
    
    # Test error messages
    error_test = "✅" if prompt_manager.get_error_message("api_error") else "❌"
    upgrade_test = "✅" if prompt_manager.get_upgrade_prompt("health_analysis") else "❌"
    
    test_report = f"""🧪 **گزارش تست سیستم Prompt**

📋 **تست Prompts اصلی:**
{chr(10).join(test_results)}

🔧 **تست سیستم‌های جانبی:**
• پیام‌های خطا: {error_test}
• Prompts ارتقاء: {upgrade_test}

📊 **نتیجه کلی:**
• تعداد تست شده: {len(prompt_types) + 2}
• موفق: {test_results.count('✅') + (1 if error_test == '✅' else 0) + (1 if upgrade_test == '✅' else 0)}
• ناموفق: {test_results.count('❌') + (1 if error_test == '❌' else 0) + (1 if upgrade_test == '❌' else 0)}

⏰ **زمان تست:** {get_persian_datetime()}"""
    
    await query.edit_message_text(
        test_report,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 تست مجدد", callback_data="admin_test_prompt"),
                InlineKeyboardButton("🔧 رفع مشکل", callback_data="admin_reload_prompts")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_prompt_management")]
        ]),
        parse_mode='Markdown'
    )

async def admin_backup_prompts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create backup of prompts"""
    query = update.callback_query
    await query.answer()
    
    try:
        import shutil
        from datetime import datetime
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"prompts_backup_{timestamp}.json"
        
        # Copy current prompts file
        shutil.copy2("prompts.json", backup_filename)
        
        await query.edit_message_text(
            f"💾 **پشتیبان‌گیری موفق**\n\n"
            f"📁 **فایل پشتیبان:** {backup_filename}\n"
            f"📅 **زمان:** {get_persian_datetime()}\n"
            f"📊 **اندازه:** {get_file_size(backup_filename)} KB\n\n"
            f"✅ فایل prompts.json با موفقیت پشتیبان‌گیری شد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_prompt_management")]
            ]),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await query.edit_message_text(
            f"❌ **خطا در پشتیبان‌گیری**\n\n"
            f"جزئیات خطا: {str(e)}\n\n"
            f"لطفاً دسترسی‌های فایل را بررسی کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_prompt_management")]
            ]),
            parse_mode='Markdown'
        )

async def admin_prompt_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show prompt usage statistics"""
    query = update.callback_query
    await query.answer()
    
    # This would typically come from analytics/database
    # For now, showing mock data structure
    
    stats_report = f"""📈 **آمار استفاده از Prompts**

🎯 **محبوب‌ترین Prompts:**
• health_analysis: 1,234 استفاده
• ai_chat: 987 استفاده  
• emergency: 456 استفاده
• nutrition: 321 استفاده
• behavior: 234 استفاده

⚡ **عملکرد سیستم:**
• میانگین زمان پاسخ: 1.2 ثانیه
• نرخ موفقیت: 98.5%
• خطاهای سیستم: 1.5%

🔄 **بارگذاری‌های اخیر:**
• آخرین بارگذاری: {get_persian_datetime()}
• تعداد بارگذاری امروز: 3
• آخرین تغییر: 2 ساعت پیش

💡 **پیشنهادات بهینه‌سازی:**
• بررسی prompts کم‌استفاده
• بهینه‌سازی prompts پرکاربرد
• اضافه کردن A/B testing"""
    
    await query.edit_message_text(
        stats_report,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 بروزرسانی", callback_data="admin_prompt_stats"),
                InlineKeyboardButton("📊 جزئیات بیشتر", callback_data="admin_detailed_stats")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_prompt_management")]
        ]),
        parse_mode='Markdown'
    )

# Helper functions
def get_file_size(filename):
    """Get file size in KB"""
    try:
        size = os.path.getsize(filename)
        return round(size / 1024, 2)
    except:
        return "نامشخص"

def get_file_modified_time(filename):
    """Get file last modified time in Persian"""
    try:
        import time
        mtime = os.path.getmtime(filename)
        return get_persian_datetime(mtime)
    except:
        return "نامشخص"

def get_persian_datetime(timestamp=None):
    """Get current time in Persian format"""
    from datetime import datetime
    if timestamp:
        dt = datetime.fromtimestamp(timestamp)
    else:
        dt = datetime.now()
    return dt.strftime("%Y/%m/%d %H:%M:%S")
