"""
Vercel serverless function for Telegram bot webhook.
"""
import json
import os
import logging
import traceback
from flask import Flask, request, jsonify
import telebot
from user_storage import initialize_user_storage

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize bot with token from environment
token = os.environ.get("TELEGRAM_BOT_TOKEN")
if not token:
    logger.error("No TELEGRAM_BOT_TOKEN set in environment variables")

# Initialize the bot if token is available
from bot import create_bot
bot = create_bot(token) if token else None

# Initialize storage
try:
    initialize_user_storage()
except Exception as e:
    logger.error(f"Error initializing storage: {str(e)}")

@app.route('/', methods=['GET'])
def home():
    """Health check endpoint."""
    return jsonify({"status": "alive", "service": "Telegram Bot Webhook"})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Process webhook updates from Telegram."""
    if not bot:
        return jsonify({"error": "Bot not initialized. Missing TELEGRAM_BOT_TOKEN"}), 500
        
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return jsonify({"status": "success"})
        except Exception as e:
            logger.error(f"Error processing update: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid content type"}), 400

@app.route('/set-webhook', methods=['GET'])
def set_webhook():
    """Set webhook URL for the bot."""
    if not bot:
        return jsonify({"error": "Bot not initialized. Missing TELEGRAM_BOT_TOKEN"}), 500
        
    try:
        # Get custom URL or construct from request
        url = request.args.get('url')
        if not url:
            host = request.headers.get('x-forwarded-host', request.host)
            proto = request.headers.get('x-forwarded-proto', 'https')
            url = f"{proto}://{host}/api/webhook"
            
        # Set the webhook
        bot.remove_webhook()
        bot.set_webhook(url=url)
        return jsonify({
            "success": True,
            "webhook_url": url
        })
    except Exception as e:
        logger.error(f"Error setting webhook: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# For Vercel serverless functions
def handler(event, context):
    """Handler for Vercel serverless functions."""
    return app(event['body'], event['headers'])