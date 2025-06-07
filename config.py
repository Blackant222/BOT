import os
from dotenv import load_dotenv

load_dotenv()

# API Credentials - Using environment variables for security
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", BOT_TOKEN)  # Backward compatibility
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate required environment variables
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Database
DATABASE_PATH = "data/petmagix.db"

# Persian Text Constants
MESSAGES = {
    "start": "🐾 سلام! به PetMagix خوش آمدید\n\nمن دستیار سلامت حیوان خانگی شما هستم. چه کاری می‌تونم براتون انجام بدم؟",
    "main_menu": "📋 منوی اصلی:",
    "add_pet": "🐕 افزودن حیوان خانگی",
    "health_log": "📊 ثبت سلامت روزانه", 
    "ai_chat": "💬 چت با دامپزشک",
    "health_analysis": "🔍 تحلیل سلامت",
    "reminders": "⏰ یادآورها",
    "error": "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید."
}

# OpenAI Settings
OPENAI_MODEL = "gpt-4.1-nano-2025-04-14"
OPENAI_MAX_TOKENS = 500
