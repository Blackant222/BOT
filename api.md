# 🔑 API Configuration Guide

This document contains the API keys and configuration details for PetMagix bot.

## 🤖 Telegram Bot Configuration

### Bot Information
- **Bot Name**: petmagix test
- **Bot Username**: @petmagixtest_bot
- **Bot Token**: `your_telegram_bot_token_here`

### Bot Setup
1. Created via @BotFather on Telegram
2. Configured with appropriate permissions
3. Webhook disabled (using polling)

## 🧠 OpenAI API Configuration

### API Details
- **API Key**: `your_openai_api_key_here`
- **Model Used**: `gpt-4.1-nano-2025-04-14`
- **Max Tokens**: 500-2000 (depending on feature)
- **Organization**: Personal account

### Model Configuration
```python
# Primary model for all features
OPENAI_MODEL = "gpt-4.1-nano-2025-04-14"

# Model usage by feature:
# - Health Analysis (Free): gpt-4.1-nano-2025-04-14
# - Health Analysis (Premium): gpt-4.1-nano-2025-04-14
# - AI Chat (Free): gpt-4.1-nano-2025-04-14
# - AI Chat (Premium): gpt-4.1-nano-2025-04-14
# - Emergency: gpt-4.1-nano-2025-04-14
# - Nutrition: gpt-4.1-nano-2025-04-14
# - Behavior: gpt-4.1-nano-2025-04-14
# - General: gpt-4.1-nano-2025-04-14
```

## ⚙️ Configuration Setup

### 1. Environment Variables (Optional)
```bash
export BOT_TOKEN="your_telegram_bot_token_here"
export OPENAI_API_KEY="your_openai_api_key_here"
```

### 2. Direct Configuration (config.py)
```python
# API Credentials
BOT_TOKEN = "your_telegram_bot_token_here"
TELEGRAM_TOKEN = "your_telegram_bot_token_here"  # Backward compatibility
OPENAI_API_KEY = "your_openai_api_key_here"

# OpenAI Settings
OPENAI_MODEL = "gpt-4.1-nano-2025-04-14"
OPENAI_MAX_TOKENS = 500
```

## 🔒 Security Notes

### API Key Security
- **Never commit API keys to public repositories**
- **Use environment variables in production**
- **Rotate keys regularly**
- **Monitor API usage for unusual activity**

### Bot Security
- **Enable webhook security in production**
- **Implement rate limiting**
- **Validate all user inputs**
- **Log security events**

## 📊 API Usage Monitoring

### OpenAI API Limits
- **Model**: gpt-4.1-nano-2025-04-14
- **Rate Limits**: Check OpenAI dashboard
- **Cost Monitoring**: Monitor token usage
- **Error Handling**: Implemented in `utils/openai_client.py`

### Telegram API Limits
- **Message Rate**: 30 messages per second
- **Bot API**: Standard limits apply
- **File Uploads**: 50MB max per file
- **Error Handling**: Built into python-telegram-bot

## 🛠️ Troubleshooting

### Common Issues

1. **OpenAI 404 Errors**
   - Verify model name is correct: `gpt-4.1-nano-2025-04-14`
   - Check API key validity
   - Ensure sufficient credits

2. **Telegram Connection Issues**
   - Verify bot token format
   - Check network connectivity
   - Ensure bot is not blocked

3. **Hot-Reload Issues**
   - Check `prompts.json` syntax
   - Verify file permissions
   - Monitor console for reload messages

### Testing Configuration
```bash
# Test Telegram connection
python -c "from telegram import Bot; print(Bot('your_telegram_bot_token_here').get_me())"

# Test OpenAI connection
python -c "from openai import OpenAI; client = OpenAI(api_key='your_openai_api_key_here'); print('OpenAI connected')"
```

## 📝 Configuration Checklist

- [ ] Telegram bot token configured
- [ ] OpenAI API key configured
- [ ] Model name verified: `gpt-4.1-nano-2025-04-14`
- [ ] Database path accessible
- [ ] Prompts.json file present
- [ ] All dependencies installed
- [ ] Bot permissions set correctly

## 🔄 Updating Configuration

### Changing API Keys
1. Update `config.py` with new keys
2. Restart the bot
3. Test functionality
4. Update this documentation

### Changing Models
1. Update `OPENAI_MODEL` in `config.py`
2. Update model names in `prompts.json`
3. Test with hot-reload (no restart needed)
4. Monitor for errors

---

**⚠️ IMPORTANT**: Keep this file secure and never share API keys publicly!
