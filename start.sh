#!/bin/bash

# Make sure we're in the right directory
cd /opt/render/project/src/petmagix-telegram-bot

# Create data directory if it doesn't exist
mkdir -p data

# Start the bot
python main.py
