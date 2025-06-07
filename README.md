# 🐾 PetMagix - AI-Powered Pet Care Assistant

**PetMagix** is an advanced Telegram bot that provides comprehensive veterinary consultation and health management for pets using AI technology. Built with Python and powered by OpenAI's language models, it offers both free and premium tiers of service.

## 🌟 Features

### 🏥 **Veterinary Consultation**
- **AI Chat**: Real-time consultation with Dr. VetX AI veterinarian
- **Health Analysis**: Comprehensive health data analysis and insights
- **Emergency Support**: 24/7 emergency triage and first aid guidance
- **Specialized Consultations**: Nutrition, behavior, and general care advice

### 📊 **Health Management**
- **Pet Profiles**: Complete pet information management
- **Health Tracking**: Daily health logging and monitoring
- **Analytics**: Advanced health trend analysis
- **Reminders**: Automated care reminders and notifications

### 🎯 **Smart Features**
- **Hot-Reloadable Prompts**: Real-time AI prompt updates without restart
- **Tier-Based Service**: Free and premium consultation levels
- **Persian Language**: Full support for Persian/Farsi users
- **Admin Dashboard**: Comprehensive management interface

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Telegram Bot Token
- OpenAI API Key

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd petmagix
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure API keys** (see `api.md` for details)
```bash
# Edit config.py with your tokens
BOT_TOKEN = "your_telegram_bot_token"
OPENAI_API_KEY = "your_openai_api_key"
```

4. **Run the bot**
```bash
python main.py
```

## 📱 Usage

### For Users
1. Start a chat with your bot on Telegram
2. Use `/start` to begin
3. Add your pet information
4. Access health tracking, AI consultation, and more

### For Admins
- Access admin panel through special commands
- Manage prompts in real-time via `prompts.json`
- Monitor analytics and user activity
- Configure subscription tiers

## 🏗️ Architecture

### Core Components
- **`main.py`**: Bot initialization and handler setup
- **`handlers/`**: Feature-specific message handlers
- **`utils/`**: Utility functions and database management
- **`prompts.json`**: AI prompt configurations with hot-reload
- **`config.py`**: Configuration and API credentials

### Key Technologies
- **Python-Telegram-Bot**: Telegram API integration
- **OpenAI API**: AI-powered veterinary consultation
- **SQLite**: Local database for user and pet data
- **APScheduler**: Automated reminders and tasks

## 🔧 Configuration

The bot uses a sophisticated prompt management system that allows real-time updates:

- **Hot-Reload**: Modify `prompts.json` and changes apply instantly
- **Tier Management**: Separate prompts for free and premium users
- **Model Configuration**: Easy switching between OpenAI models
- **Persian Support**: Localized responses and error messages

## 📊 Features Overview

| Feature | Free Tier | Premium Tier |
|---------|-----------|--------------|
| Basic Health Analysis | ✅ | ✅ |
| AI Chat Consultation | Limited | Unlimited |
| Advanced Health Insights | ❌ | ✅ |
| Emergency Support | ✅ | ✅ |
| Detailed Reports | ❌ | ✅ |
| Priority Support | ❌ | ✅ |

## 🛠️ Development

### Project Structure
```
petmagix/
├── main.py                 # Bot entry point
├── config.py              # Configuration
├── prompts.json           # AI prompts (hot-reloadable)
├── requirements.txt       # Dependencies
├── handlers/              # Message handlers
│   ├── ai_chat.py
│   ├── health_analysis.py
│   ├── health_tracking.py
│   ├── pet_management.py
│   ├── reminders.py
│   ├── subscription.py
│   └── admin_*.py
├── utils/                 # Utilities
│   ├── database.py
│   ├── openai_client.py
│   ├── prompt_manager.py
│   ├── analytics.py
│   └── keyboards.py
├── data/                  # Database
│   └── petmagix.db
└── analytics/             # Analytics data
    └── *.json
```

### Adding New Features
1. Create handler in `handlers/`
2. Add prompts to `prompts.json`
3. Register handler in `main.py`
4. Update database schema if needed

## 📈 Analytics

The bot includes comprehensive analytics:
- User activity tracking
- Health action monitoring
- Daily usage summaries
- Performance metrics

## 🔒 Security

- API keys stored in configuration files
- User data encrypted in database
- Admin access controls
- Rate limiting and abuse prevention

## 🌍 Localization

Currently supports:
- **Persian/Farsi**: Complete localization
- **English**: Technical documentation

## 📞 Support

For technical support or questions:
- Check the documentation in this repository
- Review `api.md` for configuration help
- Contact the development team

## 📄 License

This project is proprietary software. All rights reserved.

---

**Built with ❤️ for pet lovers everywhere**
