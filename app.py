import os
from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

@app.route('/')
def index():
    """Home page - provides information about the Telegram bot."""
    # Get bot username from environment if available
    bot_username = os.environ.get("BOT_USERNAME", "YourBotUsername")
    return render_template('index.html', bot_username=bot_username)

# For Vercel serverless functions
def handler(event, context):
    """Handler for Vercel serverless functions."""
    return app(event['body'], event['headers'])

# This file is meant to be imported by main.py when run through the gunicorn server
# If run directly, start the development server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)