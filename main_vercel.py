"""
Main entry point for Vercel deployment of the Telegram Bot.
This file serves both the web interface and acts as a handler for serverless functions.
"""
import os
import logging
from flask import Flask, request, jsonify, render_template
from api.webhook import app as webhook_app

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__, 
            static_folder="static",
            template_folder="templates")

# Home page
@app.route('/')
def index():
    """Home page - provides information about the Telegram bot."""
    return render_template('index.html')

# Register webhook routes
app.register_blueprint(webhook_app, url_prefix='/api')

# Handler for vercel serverless function
def handler(request, context):
    """Handle requests in a serverless context."""
    return app(request['env'], request['start_response'])

# For local development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))