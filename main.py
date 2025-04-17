"""
Main entry point for the Telegram Bot application.
This file initializes and runs the bot using pyTelegramBotAPI (telebot).
It also serves as a Flask web application to provide information about the bot.
"""
import os
import logging
import threading
from dotenv import load_dotenv
from bot import create_bot, start_bot
from app import app

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run_bot():
    """Initialize and start the Telegram bot in a separate thread."""
    # Load environment variables
    load_dotenv()
    
    # Get the token from environment variables
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No bot token provided. Set the TELEGRAM_BOT_TOKEN environment variable.")
        return
    
    # Create and start the bot
    bot = create_bot(token)
    logger.info("Bot created successfully, starting...")
    try:
        # Start the bot with polling
        start_bot(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")

def start_bot_thread():
    """Start the bot in a separate thread if the token is available."""
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        logger.info("Bot thread started")
    else:
        logger.warning("Bot not started - TELEGRAM_BOT_TOKEN not set")

# Start the bot in a separate thread when the module is imported
start_bot_thread()

if __name__ == '__main__':
    # If running this file directly, start both the bot and the Flask app
    run_bot()
