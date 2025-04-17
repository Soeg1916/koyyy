"""
Web application for the Telegram Bot service.
This file provides a simple web interface and webhook endpoints for the bot.
"""
import os
import logging
import threading
from flask import Flask, request, jsonify, render_template
import telebot
from bot import create_bot
from user_storage import initialize_user_storage
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize storage
initialize_user_storage()

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "telegram-bot-secret")

# Initialize the bot
token = os.environ.get("TELEGRAM_BOT_TOKEN")
if not token:
    logger.error("No TELEGRAM_BOT_TOKEN environment variable found.")
    bot = None
else:
    bot = create_bot(token)

@app.route('/')
def index():
    """Home page with bot information."""
    bot_username = os.environ.get("BOT_USERNAME", "Unknown")
    return render_template('index.html', bot_username=bot_username)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle webhook requests from Telegram."""
    if not bot:
        return jsonify({"error": "Bot not initialized"}), 500
        
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return jsonify({"status": "success"})
    else:
        return jsonify({"error": "Invalid content type"}), 400

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Set the webhook for the bot."""
    if not bot:
        return jsonify({"error": "Bot not initialized"}), 500
        
    # Get the URL from the request if provided, otherwise construct from request
    url = request.args.get('url')
    if not url:
        host = request.headers.get('x-forwarded-host', request.host)
        proto = request.headers.get('x-forwarded-proto', 'https')
        url = f"{proto}://{host}/webhook"
    
    try:
        bot.remove_webhook()
        bot.set_webhook(url=url)
        return jsonify({
            "status": "success",
            "message": f"Webhook set to {url}"
        })
    except Exception as e:
        logger.error(f"Error setting webhook: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to set webhook: {str(e)}"
        }), 500

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "bot_initialized": bot is not None
    })

if __name__ == '__main__':
    # Run the Flask app for the web interface
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)