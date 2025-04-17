"""
Main entry point for the Telegram Bot application.
This file initializes and runs the bot using pyTelegramBotAPI (telebot)
when run directly, or serves as a Flask web application when imported.
"""
import os
import logging
import threading
from dotenv import load_dotenv
from bot import create_bot, start_bot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global variable to track if we're running the bot or the web app
is_bot_running = False

def run_bot():
    """Initialize and start the Telegram bot."""
    global is_bot_running
    
    # Avoid running multiple instances
    if is_bot_running:
        logger.warning("Bot is already running, skipping additional instance")
        return
        
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
        # Mark as running
        is_bot_running = True
        # Start the bot with polling
        start_bot(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        is_bot_running = False

# Only start the bot when this file is run directly
if __name__ == '__main__':
    run_bot()
else:
    # This means we're being imported by the Flask app
    from app import app
