"""
Main entry point for the Telegram Bot application.
This file initializes and runs the bot using pyTelegramBotAPI (telebot).
"""
import os
import logging
from dotenv import load_dotenv
from bot import create_bot, start_bot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Initialize and start the Telegram bot."""
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

if __name__ == '__main__':
    main()
