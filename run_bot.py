#!/usr/bin/env python3
"""
PetMagix Telegram Bot - Simple Startup Script
"""
import sys
import os

def check_requirements():
    """Check if all required dependencies are installed"""
    try:
        import telegram
        import openai
        import pandas
        import sklearn
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("Copy .env.example to .env and fill in your tokens:")
        print("cp .env.example .env")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not bot_token:
        print("❌ BOT_TOKEN not set in .env file")
        return False
    
    if not openai_key:
        print("❌ OPENAI_API_KEY not set in .env file")
        return False
    
    print("✅ Environment variables configured")
    return True

def main():
    """Main startup function"""
    print("🐾 PetMagix Telegram Bot Startup")
    print("=" * 40)
    
    # Check dependencies
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    if not check_env_file():
        sys.exit(1)
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('analytics', exist_ok=True)
    
    print("🚀 Starting bot...")
    print("Press Ctrl+C to stop")
    print("=" * 40)
    
    # Import and run the main bot
    from main import main as run_bot
    run_bot()

if __name__ == "__main__":
    main()
