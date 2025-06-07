# 🚀 PetMagix Telegram Bot - Render.com Deployment Guide

## 📋 Prerequisites

Before deploying to Render.com, make sure you have:

1. **Telegram Bot Token** - Get from [@BotFather](https://t.me/botfather)
2. **OpenAI API Key** - Get from [OpenAI Platform](https://platform.openai.com/api-keys)
3. **GitHub Repository** - Your code should be in a GitHub repo
4. **Render.com Account** - Sign up at [render.com](https://render.com)

## 🔧 Files Created for Deployment

### 1. `start.sh` - Startup Script
```bash
#!/bin/bash
cd /opt/render/project/src/petmagix-telegram-bot
mkdir -p data
python main.py
```

### 2. `render.yaml` - Render Configuration
- Defines the service type, build commands, and environment variables
- Sets up persistent disk storage for the database
- Configures the Python environment

### 3. `.env` - Environment Variables (Local Development)
- Contains your API keys for local testing
- **⚠️ Never commit this to Git!**

### 4. `.env.example` - Template for Environment Variables
- Shows what environment variables are needed
- Safe to commit to Git

### 5. `.gitignore` - Git Ignore Rules
- Protects sensitive files from being committed
- Excludes database files, logs, and environment variables

## 🚀 Deployment Steps

### Step 1: Push to GitHub
```bash
cd petmagix-telegram-bot
git init
git add .
git commit -m "Initial commit - Ready for Render deployment"
git branch -M main
git remote add origin https://github.com/yourusername/petmagix-telegram-bot.git
git push -u origin main
```

### Step 2: Deploy on Render.com

1. **Login to Render.com**
   - Go to [render.com](https://render.com)
   - Sign in with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `petmagix-telegram-bot` repository

3. **Configure Service**
   - **Name**: `petmagix-telegram-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `bash start.sh`
   - **Plan**: Free (or paid for better performance)

4. **Set Environment Variables**
   In the Render dashboard, add these environment variables:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   TELEGRAM_TOKEN=your_telegram_bot_token_here
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_PATH=data/petmagix.db
   ```

5. **Add Persistent Disk (Important!)**
   - Go to "Disks" tab in your service
   - Add disk: Name: `petmagix-data`, Size: `1GB`, Mount Path: `/opt/render/project/src/petmagix-telegram-bot/data`

6. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete

## 🔍 Monitoring & Debugging

### Check Logs
- In Render dashboard, go to your service
- Click "Logs" tab to see real-time logs
- Look for startup messages:
  ```
  🤖 Pet Care Bot is starting...
  📱 Bot token configured: 7774075410...
  🗄️ Database path: data/petmagix.db
  🤖 OpenAI configured: Yes
  🚀 Bot is running! Press Ctrl+C to stop.
  ```

### Common Issues & Solutions

1. **Bot not responding**
   - Check if BOT_TOKEN is correctly set
   - Verify the bot is not running elsewhere
   - Check logs for error messages

2. **Database errors**
   - Ensure persistent disk is properly mounted
   - Check DATABASE_PATH environment variable
   - Verify data directory permissions

3. **OpenAI errors**
   - Verify OPENAI_API_KEY is valid
   - Check API quota and billing
   - Monitor API usage in OpenAI dashboard

## 🔄 Updates & Maintenance

### Updating the Bot
1. Make changes to your code
2. Commit and push to GitHub
3. Render will automatically redeploy

### Manual Redeploy
- In Render dashboard, click "Manual Deploy" → "Deploy latest commit"

### Environment Variables Update
- Go to "Environment" tab in Render dashboard
- Update variables as needed
- Service will restart automatically

## 📊 Features Included

Your bot includes these features:
- 🐕 Pet management system
- 📊 Health tracking and analytics
- 🤖 AI-powered veterinary chat
- 🔍 Health analysis and insights
- ⏰ Medication and care reminders
- 💳 Subscription management
- 📈 Admin analytics dashboard

## 🛡️ Security Notes

- ✅ API keys are stored as environment variables
- ✅ Sensitive files are excluded from Git
- ✅ Database is stored on persistent disk
- ✅ Logs don't expose sensitive information

## 🆘 Support

If you encounter issues:
1. Check the logs in Render dashboard
2. Verify all environment variables are set
3. Ensure your GitHub repository is up to date
4. Test the bot locally first using the .env file

## 🎉 Success!

Once deployed successfully, your bot will be running 24/7 on Render.com and users can interact with it via Telegram!

Bot Username: Search for your bot on Telegram using the username you set with @BotFather.
