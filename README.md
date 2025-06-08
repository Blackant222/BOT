# 🐾 PetMagix Telegram Bot

A comprehensive Telegram bot for pet health management with AI-powered insights, health tracking, and smart reminders.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your tokens:
# BOT_TOKEN=your_telegram_bot_token_here
# OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run the Bot
```bash
# Simple startup with checks
python run_bot.py

# Or run directly
python main.py
```

## 🔧 Configuration

### Required Environment Variables
- `BOT_TOKEN`: Your Telegram bot token from @BotFather
- `OPENAI_API_KEY`: Your OpenAI API key for AI features

### Optional Configuration
- `DATABASE_PATH`: Custom database path (defaults to `data/petmagix.db`)

## 📁 Project Structure

```
petmagix-telegram-bot/
├── main.py                 # Main bot entry point
├── config.py              # Configuration and settings
├── run_bot.py             # Startup script with checks
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── handlers/             # Bot command handlers
│   ├── ai_chat.py        # AI chat functionality
│   ├── health_tracking.py # Health logging
│   ├── pet_management.py  # Pet CRUD operations
│   ├── health_analysis.py # Health insights
│   ├── reminders.py      # Smart reminders
│   ├── subscription.py   # Premium features
│   └── admin_analytics.py # Admin tools
├── utils/                # Utility modules
│   ├── database.py       # Database operations
│   ├── openai_client.py  # AI client
│   ├── analytics.py      # Usage analytics
│   ├── keyboards.py      # Telegram keyboards
│   ├── persian_utils.py  # Persian text utils
│   └── prompt_manager.py # AI prompt management
├── data/                 # Database storage
└── analytics/           # Analytics logs
```

## 🤖 Features

### 🐕 Pet Management
- Add multiple pets with detailed profiles
- Track species, breed, age, weight, medical history
- Vaccination and medication tracking

### 📊 Health Tracking
- Daily health logging (weight, mood, appetite, etc.)
- Photo uploads for vet records
- Stool quality and breathing monitoring
- Custom health notes

### 🔍 AI-Powered Analysis
- Health score calculation (0-100)
- Symptom pattern recognition
- Predictive health insights
- Emergency situation detection

### 💬 Smart AI Chat
- Specialized veterinary consultation
- Emergency mode for urgent issues
- Nutrition and behavior guidance
- Context-aware responses

### ⏰ Smart Reminders
- Medication schedules
- Vaccination alerts
- Daily health check reminders
- Customizable notification settings

### 📈 Analytics & Insights
- Health trend analysis
- Behavioral pattern tracking
- Admin analytics dashboard
- Data export capabilities

## 🛠️ Development

### Database
- SQLite database with automatic initialization
- Stores user data, pets, health logs, and analytics
- Located at `data/petmagix.db`

### AI Integration
- OpenAI GPT-4.1 Nano for cost-effective responses
- Specialized prompts for veterinary advice
- Context-aware conversation handling

### Analytics
- Real-time usage tracking
- Performance monitoring
- Error logging and debugging
- Daily analytics summaries

## 🔒 Security

- Environment variables for sensitive data
- No hardcoded API keys
- User data isolation
- Secure database operations

## 📝 Admin Commands

- `/analytics` - View usage statistics
- `/detailed_analytics` - Comprehensive analytics
- `/export_analytics` - Export data
- `/clear_analytics` - Clear analytics data

## 🐛 Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check BOT_TOKEN in .env file
   - Verify bot is started with @BotFather

2. **AI features not working**
   - Verify OPENAI_API_KEY in .env file
   - Check OpenAI account credits

3. **Database errors**
   - Ensure `data/` directory exists
   - Check file permissions

### Logs
- Bot logs are displayed in console
- Error tracking in analytics files
- Use `/analytics` command for debugging

## 📄 License

This project is for educational and personal use.
