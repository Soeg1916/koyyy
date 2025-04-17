"""
Webhook handler for Telegram bot deployed on Vercel.
This file handles incoming webhook requests from Telegram.
"""
import json
import os
import logging
import telebot
from flask import Blueprint, request, jsonify
from user_storage import initialize_user_storage
import traceback

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask Blueprint
app = Blueprint('webhook', __name__)

# Initialize bot with token from environment
token = os.environ.get("TELEGRAM_BOT_TOKEN")
if not token:
    raise ValueError("No TELEGRAM_BOT_TOKEN set in environment variables")

# Initialize the bot (import here to avoid circular import)
from bot import create_bot
bot = create_bot(token)

# Initialize storage
initialize_user_storage()

@app.route('/', methods=['GET'])
def index():
    """Home page for the webhook."""
    return "Telegram bot webhook is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook requests from Telegram."""
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return jsonify({"status": "success"})
        except Exception as e:
            logger.error(f"Error processing update: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"status": "error", "message": str(e)})
    else:
        return jsonify({"status": "error", "message": "Invalid content type"})

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Set the webhook URL for the bot."""
    try:
        webhook_url = request.args.get('url')
        if not webhook_url:
            # For Vercel deployments, construct webhook URL from headers
            host = request.headers.get('x-forwarded-host', request.host)
            proto = request.headers.get('x-forwarded-proto', 'https')
            webhook_url = f"{proto}://{host}/api/webhook"
        
        # Set webhook
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        return jsonify({
            "status": "success", 
            "message": f"Webhook set to {webhook_url}"
        })
    except Exception as e:
        logger.error(f"Error setting webhook: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)})

# For local testing
if __name__ == '__main__':
    app.run(debug=True)