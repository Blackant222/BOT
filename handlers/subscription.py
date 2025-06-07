"""
💎 SUBSCRIPTION & MONETIZATION SYSTEM
Real database-backed subscription system with premium features
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import random
from utils.database import db
from utils.keyboards import main_menu_keyboard
from utils.persian_utils import persian_number

# Subscription states
CHECK_SUBSCRIPTION, PAYMENT_METHOD, CONFIRM_PAYMENT = range(3)

def check_user_subscription(user_id):
    """Check if user has active premium subscription - REAL DATABASE"""
    return db.get_user_subscription(user_id)

def is_premium_feature_blocked(user_id, feature_type):
    """Check if feature is blocked for free users - REAL DATABASE"""
    subscription = check_user_subscription(user_id)
    
    if subscription['is_premium']:
        return False
    
    # Define what's blocked for free users
    blocked_features = {
        'multiple_pets': True,  # Only 1 pet for free users
        'unlimited_ai_chat': True,  # Limited AI chat
        'image_upload': True,  # No image uploads
        'advanced_analysis': True,  # Basic analysis only
        'custom_reminders': True,  # Basic reminders only
        'export_reports': True  # No PDF exports
    }
    
    return blocked_features.get(feature_type, False)

async def show_subscription_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current subscription status"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    subscription = check_user_subscription(user_id)
    
    if subscription['is_premium']:
        # Calculate days remaining
        if subscription['end_date']:
            end_date = datetime.strptime(subscription['end_date'], '%Y-%m-%d %H:%M:%S')
            days_remaining = (end_date - datetime.now()).days
        else:
            days_remaining = 999  # Unlimited
        
        trial_text = " (دوره آزمایشی)" if subscription['is_trial'] else ""
        
        status_text = f"""
💎 **وضعیت اشتراک شما**

✅ **نوع حساب**: پریمیوم{trial_text}
📅 **زمان باقی‌مانده**: {persian_number(str(days_remaining))} روز
🎯 **وضعیت**: فعال

🌟 **امکانات فعال شما:**
• حیوانات نامحدود (تا ۱۰ عدد)
• مشاوره AI نامحدود
• آپلود تصاویر و فایل‌ها
• تحلیل‌های پیشرفته
• یادآورهای سفارشی
• گزارش‌های PDF
• پشتیبانی اولویت‌دار

💡 **نکته**: اشتراک شما تا {subscription['end_date'][:10] if subscription['end_date'] else 'نامحدود'} فعال است.
        """
    else:
        status_text = f"""
👤 **وضعیت اشتراک شما**

⚠️ **نوع حساب**: رایگان
🎁 **امکانات فعلی**: محدود

📋 **امکانات رایگان:**
• ۱ حیوان خانگی
• ثبت سلامت روزانه
• ۳ پیام AI در روز
• تحلیل پایه‌ای
• یادآورهای ساده

🚀 **با ارتقاء به پریمیوم دریافت کنید:**
• ۱۰ حیوان همزمان
• مشاوره AI نامحدود
• آپلود تصاویر آزمایش
• تحلیل‌های هوشمند
• یادآورهای پیشرفته
• گزارش‌های تخصصی

💰 **قیمت**: فقط ۵۹ هزار تومان/ماه
        """
    
    keyboard = []
    if not subscription['is_premium']:
        keyboard.append([InlineKeyboardButton("🚀 ارتقاء به پریمیوم", callback_data="upgrade_premium")])
    
    keyboard.append([InlineKeyboardButton("🏠 بازگشت به منو", callback_data="back_main")])
    
    await query.edit_message_text(
        status_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_premium_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium upgrade options"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    subscription = check_user_subscription(user_id)
    
    # Check if user already has trial
    trial_used = subscription['is_trial'] or subscription['subscription_type'] == 'trial'
    
    upgrade_text = """
💎 **ارتقاء به نسخه پریمیوم**

🎯 **چرا پریمیوم؟**
✅ مراقبت حرفه‌ای از حیوان خانگی
✅ تشخیص زودهنگام مشکلات
✅ صرفه‌جویی در هزینه‌های دامپزشکی
✅ آرامش خیال کامل

💰 **پلان‌های قیمتی:**

🔸 **۱ ماهه**: ۵۹,۰۰۰ تومان
🔸 **۳ ماهه**: ۱۶۵,۰۰۰ تومان (۱۲٪ تخفیف)
🔸 **۶ ماهه**: ۳۱۵,۰۰۰ تومان (۱۵٪ تخفیف)
🔸 **۱ ساله**: ۴۵۰,۰۰۰ تومان (۳۶٪ تخفیف)

💳 **پرداخت امن**: زرین‌پال، بانک‌های ایرانی
    """
    
    keyboard = []
    
    # Add trial button only if not used
    if not trial_used:
        upgrade_text += "\n🎁 **ویژه امروز**: ۷ روز رایگان برای تست!"
        keyboard.append([InlineKeyboardButton("🎁 شروع ۷ روز رایگان", callback_data="free_trial")])
    
    keyboard.extend([
        [InlineKeyboardButton("💳 ۱ ماه - ۵۹ هزار تومان", callback_data="pay_1month")],
        [InlineKeyboardButton("💎 ۳ ماه - ۱۶۵ هزار تومان", callback_data="pay_3month")],
        [InlineKeyboardButton("🏆 ۱ سال - ۴۵۰ هزار تومان", callback_data="pay_1year")],
        [InlineKeyboardButton("🏠 بازگشت", callback_data="subscription_status")]
    ])
    
    await query.edit_message_text(
        upgrade_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def start_free_trial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start 7-day free trial - REAL DATABASE"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    subscription = check_user_subscription(user_id)
    
    # Check if trial already used
    if subscription['is_trial'] or subscription['subscription_type'] == 'trial':
        await query.edit_message_text(
            "❌ شما قبلاً از دوره آزمایشی استفاده کرده‌اید.\n"
            "برای ادامه، اشتراک پریمیوم تهیه کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 خرید پریمیوم", callback_data="upgrade_premium")],
                [InlineKeyboardButton("🏠 بازگشت", callback_data="back_main")]
            ])
        )
        return
    
    # Start trial in database
    db.start_trial(user_id)
    
    trial_end = (datetime.now() + timedelta(days=7)).strftime('%Y/%m/%d')
    
    trial_text = f"""
🎉 **تبریک! دوره آزمایشی فعال شد**

✅ **۷ روز پریمیوم رایگان** برای شما فعال شد!
📅 **تاریخ انقضا**: {persian_number(trial_end)}
🎯 **وضعیت**: فعال

🌟 **اکنون می‌توانید استفاده کنید از:**
• مشاوره AI نامحدود
• آپلود تصاویر آزمایش
• تحلیل‌های پیشرفته
• یادآورهای سفارشی
• گزارش‌های تخصصی

💡 **نکته**: ۲ روز قبل از پایان، یادآوری خواهیم داد.

🎯 **برای ادامه استفاده، اشتراک خود را تمدید کنید.**
    """
    
    keyboard = [
        [InlineKeyboardButton("🏠 شروع استفاده", callback_data="back_main")],
        [InlineKeyboardButton("💎 مشاهده پلان‌ها", callback_data="upgrade_premium")]
    ]
    
    await query.edit_message_text(
        trial_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process mock payment"""
    query = update.callback_query
    await query.answer()
    
    payment_type = query.data
    
    # Payment details
    payment_info = {
        'pay_1month': {'amount': '59,000', 'period': '۱ ماه', 'days': 30},
        'pay_3month': {'amount': '165,000', 'period': '۳ ماه', 'days': 90},
        'pay_1year': {'amount': '450,000', 'period': '۱ سال', 'days': 365}
    }
    
    info = payment_info.get(payment_type, payment_info['pay_1month'])
    
    # Generate mock payment reference
    payment_ref = f"PM{random.randint(100000, 999999)}"
    
    payment_text = f"""
💳 **تایید پرداخت**

📋 **جزئیات سفارش:**
• مدت اشتراک: {info['period']}
• مبلغ: {info['amount']} تومان
• کد پیگیری: {payment_ref}

🔐 **پرداخت امن از طریق:**
• زرین‌پال (ZarinPal)
• درگاه بانک‌های ایرانی
• رمزنگاری SSL

⚠️ **توجه**: پس از کلیک روی "پرداخت"، به درگاه امن منتقل می‌شوید.

💡 **لغو تا ۲۴ ساعت**: بازگشت کامل وجه
    """
    
    keyboard = [
        [InlineKeyboardButton("💳 پرداخت امن", callback_data=f"confirm_payment_{payment_type}")],
        [InlineKeyboardButton("❌ انصراف", callback_data="upgrade_premium")]
    ]
    
    await query.edit_message_text(
        payment_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def confirm_mock_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm mock payment (simulate successful payment) - REAL DATABASE"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Extract payment type
    payment_type = query.data.replace('confirm_payment_', '')
    
    payment_info = {
        'pay_1month': {'period': '۱ ماه', 'months': 1},
        'pay_3month': {'period': '۳ ماه', 'months': 3},
        'pay_1year': {'period': '۱ سال', 'months': 12}
    }
    
    info = payment_info.get(payment_type, payment_info['pay_1month'])
    
    # Generate payment reference
    payment_ref = f"PM{random.randint(100000, 999999)}"
    
    # Upgrade user to premium in database
    db.upgrade_to_premium(user_id, payment_ref, info['months'])
    
    # Calculate end date
    end_date = (datetime.now() + timedelta(days=30 * info['months'])).strftime('%Y/%m/%d')
    
    # Mock successful payment
    success_text = f"""
🎉 **پرداخت موفق!**

✅ **اشتراک پریمیوم فعال شد**
📅 **مدت**: {info['period']}
🗓️ **انقضا**: {persian_number(end_date)}
🎯 **وضعیت**: فعال
💳 **کد پیگیری**: {payment_ref}

🌟 **امکانات فعال شده:**
• مشاوره AI نامحدود ✅
• آپلود تصاویر و فایل‌ها ✅
• تحلیل‌های پیشرفته ✅
• یادآورهای سفارشی ✅
• گزارش‌های PDF ✅

📧 **ایمیل تایید**: ارسال شد
📱 **فاکتور**: در پیام‌های ذخیره شده

🚀 **اکنون می‌توانید از تمام امکانات استفاده کنید!**
    """
    
    keyboard = [
        [InlineKeyboardButton("🏠 شروع استفاده", callback_data="back_main")],
        [InlineKeyboardButton("📊 مشاهده وضعیت", callback_data="subscription_status")]
    ]
    
    await query.edit_message_text(
        success_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_premium_blocked_feature(update: Update, context: ContextTypes.DEFAULT_TYPE, feature_name: str):
    """Show premium upgrade prompt when feature is blocked"""
    
    blocked_text = f"""
🔒 **امکان محدود**

⚠️ **{feature_name}** فقط برای کاربران پریمیوم در دسترس است.

🎁 **با ارتقاء به پریمیوم دریافت کنید:**
• دسترسی کامل به تمام امکانات
• مشاوره نامحدود با دامپزشک AI
• آپلود تصاویر و فایل‌ها
• تحلیل‌های پیشرفته
• یادآورهای سفارشی

💰 **قیمت**: فقط ۵۹ هزار تومان/ماه
🎯 **۷ روز رایگان** برای تست!
    """
    
    keyboard = [
        [InlineKeyboardButton("🚀 ارتقاء به پریمیوم", callback_data="upgrade_premium")],
        [InlineKeyboardButton("🎁 ۷ روز رایگان", callback_data="free_trial")],
        [InlineKeyboardButton("🏠 بازگشت", callback_data="back_main")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            blocked_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            blocked_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

def add_premium_upsell_button(keyboard_rows):
    """Add premium upsell button to existing keyboard"""
    keyboard_rows.append([InlineKeyboardButton("💎 ارتقاء به پریمیوم", callback_data="upgrade_premium")])
    return keyboard_rows

# Daily usage limits for free users - REAL DATABASE
def check_daily_ai_limit(user_id):
    """Check if user has exceeded daily AI chat limit - REAL DATABASE"""
    subscription = check_user_subscription(user_id)
    
    # Premium users have no limits
    if subscription['is_premium']:
        return False
    
    # Free users limited to 3 messages per day
    usage_count = db.get_ai_usage(user_id)
    return usage_count >= 3

def get_ai_usage_count(user_id):
    """Get current AI usage count for today - REAL DATABASE"""
    return db.get_ai_usage(user_id)

def increment_ai_usage(user_id):
    """Increment AI usage count - REAL DATABASE"""
    db.increment_ai_usage(user_id)

# Manual premium activation for testing
async def activate_premium_manually(user_id, months=1):
    """Manually activate premium for testing"""
    payment_ref = f"MANUAL_{random.randint(100000, 999999)}"
    db.upgrade_to_premium(user_id, payment_ref, months)
    return f"Premium activated for user {user_id} for {months} months. Reference: {payment_ref}"

async def deactivate_premium_manually(user_id):
    """Manually deactivate premium for testing"""
    db.update_subscription(user_id, is_premium=False, subscription_type='free', end_date=None)
    return f"Premium deactivated for user {user_id}"
