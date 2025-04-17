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
from user_storage import initialize_user_storage

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
    
    # Create a log file for debugging
    with open('/tmp/bot_debug.log', 'w') as f:
        f.write(f"Bot startup: {__name__} at {os.path.abspath(__file__)}\n")
    
    # Avoid running multiple instances
    if is_bot_running:
        logger.warning("Bot is already running, skipping additional instance")
        with open('/tmp/bot_debug.log', 'a') as f:
            f.write("Bot is already running, skipping additional instance\n")
        return
        
    # Load environment variables
    load_dotenv()
    
    # Get the token from environment variables
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    token_preview = token[:6] + '...' if token else 'None'
    with open('/tmp/bot_debug.log', 'a') as f:
        f.write(f"Token: {token_preview}\n")
    
    if not token:
        logger.error("No bot token provided. Set the TELEGRAM_BOT_TOKEN environment variable.")
        with open('/tmp/bot_debug.log', 'a') as f:
            f.write("No bot token provided\n")
        return
    
    try:
        # Initialize user storage
        with open('/tmp/bot_debug.log', 'a') as f:
            f.write("Initializing user storage...\n")
        initialize_user_storage()
        
        # Create and start the bot
        with open('/tmp/bot_debug.log', 'a') as f:
            f.write("Creating bot...\n")
        bot = create_bot(token)
        logger.info("Bot created successfully, starting...")
        with open('/tmp/bot_debug.log', 'a') as f:
            f.write("Bot created successfully, starting...\n")
        
        # Mark as running
        is_bot_running = True
        
        # Start the bot with polling
        with open('/tmp/bot_debug.log', 'a') as f:
            f.write("Starting bot polling...\n")
        start_bot(bot)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        with open('/tmp/bot_debug.log', 'a') as f:
            f.write("Bot stopped by user\n")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        with open('/tmp/bot_debug.log', 'a') as f:
            f.write(f"Error running bot: {str(e)}\n")
            import traceback
            f.write(traceback.format_exc())
    finally:
        is_bot_running = False
        with open('/tmp/bot_debug.log', 'a') as f:
            f.write("Bot stopped\n")

# Only start the bot when this file is run directly
if __name__ == '__main__':
    run_bot()
else:
    # This means we're being imported by the Flask app
    from app import app
