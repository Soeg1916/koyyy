"""
Telegram bot implementation with video download, audio extraction, and media management.
Using pyTelegramBotAPI (telebot) library.
"""
import os
import logging
import json
import threading
import asyncio
import telebot
from telebot import types
from media_downloader import download_video
from audio_extractor import extract_audio
from user_storage import (
    save_media,
    retrieve_media,
    get_user_media_list,
    initialize_user_storage,
)
from utils import is_valid_url, get_media_type, sanitize_filename

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store temporary user data
user_data_store = {}

# State constants for conversation flows
WAITING_FOR_SAVE_NAME = 1
user_states = {}

def create_bot(token):
    """Create and configure the bot application."""
    # Initialize the bot
    bot = telebot.TeleBot(token)
    
    # Initialize storage
    initialize_user_storage()
    
    # Register command handlers
    @bot.message_handler(commands=['start'])
    def start_command(message):
        """Handler for /start command"""
        welcome_message = (
            "👋 Welcome to Social Media Downloader Bot!\n\n"
            "I can help you download videos from social media platforms, extract audio, and save your media.\n\n"
            "Just send me a link to a video from TikTok, Instagram, YouTube Shorts, or Pinterest.\n\n"
            "Commands:\n"
            "/help - Show help information\n"
            "/list - List your saved media\n"
            "/my [name] - Retrieve your saved media by name"
        )
        bot.reply_to(message, welcome_message)
    
    @bot.message_handler(commands=['help'])
    def help_command(message):
        """Handler for /help command"""
        help_message = (
            "📋 Bot Instructions:\n\n"
            "1️⃣ Send a link to a video from TikTok, Instagram, YouTube Shorts, or Pinterest\n"
            "2️⃣ I'll download and send you the video\n"
            "3️⃣ Use the '🎵 Download Audio' button to extract audio\n"
            "4️⃣ Use the '💾 Save' button to save media with a custom name\n"
            "5️⃣ Use /list to see all your saved media\n"
            "6️⃣ Use /my [name] to retrieve your saved media\n\n"
            "Examples:\n"
            "• Send: https://www.tiktok.com/@username/video/1234567890\n"
            "• To retrieve: /my favorite_song"
        )
        bot.reply_to(message, help_message)
    
    @bot.message_handler(commands=['list'])
    def list_command(message):
        """Handler for /list command"""
        user_id = message.from_user.id
        media_list = get_user_media_list(user_id)
        
        if not media_list:
            bot.reply_to(message, "You don't have any saved media yet.")
            return
        
        response = "📋 Your saved media:\n\n"
        for i, (name, media_type) in enumerate(media_list, 1):
            icon = "🎵" if media_type == "audio" else "🎬"
            response += f"{i}. {icon} {name}\n"
        
        response += "\nTo retrieve a file, use /my [name]"
        bot.reply_to(message, response)
    
    @bot.message_handler(commands=['my'])
    def retrieve_command(message):
        """Handler for /my [name] command"""
        user_id = message.from_user.id
        command_args = message.text.split(' ', 1)
        
        if len(command_args) < 2:
            bot.reply_to(message, "Please provide a name. Usage: /my [name]")
            return
        
        media_name = command_args[1].strip()
        result = retrieve_media(user_id, media_name)
        
        if not result:
            bot.reply_to(message, f"No media found with the name '{media_name}'.")
            return
        
        file_path, media_type = result
        
        if not os.path.exists(file_path):
            bot.reply_to(message, "Sorry, the media file could not be found.")
            return
        
        bot.send_message(message.chat.id, f"Sending your saved media: {media_name}")
        
        if media_type == "video":
            with open(file_path, 'rb') as video_file:
                bot.send_video(message.chat.id, video_file, caption=f"Your saved video: {media_name}")
        elif media_type == "audio":
            with open(file_path, 'rb') as audio_file:
                bot.send_audio(message.chat.id, audio_file, title=media_name)
    
    @bot.message_handler(func=lambda message: is_valid_url(message.text))
    def handle_url_message(message):
        """Handler for messages containing URLs"""
        url = message.text
        
        # Let the user know we're working on it
        status_message = bot.send_message(message.chat.id, "🔄 Processing your request. This may take a moment...")
        
        # Use a thread to handle the download process
        def download_thread():
            try:
                # Download the video (wrap the async function)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                video_path = loop.run_until_complete(download_video(url))
                
                if not video_path or not os.path.exists(video_path):
                    bot.edit_message_text("❌ Failed to download the video. Please check the URL and try again.",
                                         message.chat.id, status_message.message_id)
                    return
                
                # Create inline keyboard with buttons for audio extraction and saving
                markup = types.InlineKeyboardMarkup()
                extract_button = types.InlineKeyboardButton("🎵 Download Audio", 
                                                         callback_data=f"extract_audio_{video_path}")
                save_button = types.InlineKeyboardButton("💾 Save", 
                                                      callback_data=f"save_video_{video_path}")
                markup.add(extract_button, save_button)
                
                # Delete the status message
                bot.delete_message(message.chat.id, status_message.message_id)
                
                # Send the video with buttons
                with open(video_path, 'rb') as video_file:
                    bot.send_video(message.chat.id, video_file, caption="Here's your downloaded video!", 
                                 reply_markup=markup)
                
            except Exception as e:
                logger.error(f"Error downloading video: {e}")
                bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, status_message.message_id)
        
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('extract_audio_'))
    def extract_audio_callback(call):
        """Handle callback for extracting audio from a video"""
        bot.answer_callback_query(call.id)
        
        # Get the video path from the callback data
        _, video_path = call.data.split("_", 1)
        
        if not os.path.exists(video_path):
            bot.edit_message_caption(caption="⚠️ Video file no longer available.", 
                                   chat_id=call.message.chat.id, 
                                   message_id=call.message.message_id)
            return
        
        # Inform the user
        bot.edit_message_caption(caption="🔄 Extracting audio... Please wait.", 
                               chat_id=call.message.chat.id, 
                               message_id=call.message.message_id)
        
        def extract_thread():
            try:
                # Extract the audio (wrap the async function)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                audio_path = loop.run_until_complete(extract_audio(video_path))
                
                if not audio_path or not os.path.exists(audio_path):
                    bot.edit_message_caption(caption="❌ Failed to extract audio.",
                                           chat_id=call.message.chat.id,
                                           message_id=call.message.message_id)
                    return
                
                # Create inline keyboard with save button
                markup = types.InlineKeyboardMarkup()
                save_button = types.InlineKeyboardButton("💾 Save", 
                                                      callback_data=f"save_audio_{audio_path}")
                markup.add(save_button)
                
                # Send the audio file
                with open(audio_path, 'rb') as audio_file:
                    bot.send_audio(call.message.chat.id, audio_file,
                                 caption="Here's the extracted audio!",
                                 reply_markup=markup)
                
                # Restore the original video caption with its buttons
                markup = types.InlineKeyboardMarkup()
                extract_button = types.InlineKeyboardButton("🎵 Download Audio", 
                                                         callback_data=f"extract_audio_{video_path}")
                save_button = types.InlineKeyboardButton("💾 Save", 
                                                      callback_data=f"save_video_{video_path}")
                markup.add(extract_button, save_button)
                
                bot.edit_message_caption(caption="Here's your downloaded video!",
                                       chat_id=call.message.chat.id,
                                       message_id=call.message.message_id,
                                       reply_markup=markup)
                
            except Exception as e:
                logger.error(f"Error in extraction thread: {e}")
                bot.edit_message_caption(caption=f"❌ Error extracting audio: {str(e)}",
                                       chat_id=call.message.chat.id,
                                       message_id=call.message.message_id)
        
        thread = threading.Thread(target=extract_thread)
        thread.daemon = True
        thread.start()
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('save_'))
    def save_button_callback(call):
        """Handle callback for saving media"""
        bot.answer_callback_query(call.id)
        
        # Get data from callback
        data_parts = call.data.split("_", 2)
        if len(data_parts) != 3:
            bot.send_message(call.message.chat.id, "❌ Invalid data format.")
            return
        
        _, media_type, media_path = data_parts
        
        if not os.path.exists(media_path):
            bot.send_message(call.message.chat.id, "⚠️ Media file no longer available.")
            return
        
        # Store data for the conversation
        user_id = call.from_user.id
        user_data_store[user_id] = {
            "media_type": media_type,
            "media_path": media_path,
            "chat_id": call.message.chat.id
        }
        
        # Set the user's state
        user_states[user_id] = WAITING_FOR_SAVE_NAME
        
        # Ask for a name to save the media
        msg = bot.send_message(call.message.chat.id,
                            "📝 Please enter a name to save this media.\n"
                            "You'll be able to retrieve it later using /my [name]\n\n"
                            "Type /cancel to abort.")
        
        # Register the next step handler
        bot.register_next_step_handler(msg, save_media_name_handler)
    
    # Handle the media name input
    def save_media_name_handler(message):
        """Save media with the provided name"""
        # Check for /cancel command
        if message.text.startswith('/cancel'):
            return cancel_save_handler(message)
        
        user_id = message.from_user.id
        media_name = message.text.strip()
        
        # Check if the user is in the correct state
        if user_id not in user_states or user_states[user_id] != WAITING_FOR_SAVE_NAME:
            bot.reply_to(message, "❌ Session expired. Please try again.")
            return
        
        # Validate the name
        if not media_name or len(media_name) > 50:
            msg = bot.reply_to(message, "⚠️ Please provide a valid name (max 50 characters).")
            bot.register_next_step_handler(msg, save_media_name_handler)
            return
        
        # Get the stored media information
        user_data = user_data_store.get(user_id)
        if not user_data:
            bot.reply_to(message, "❌ Session expired. Please try again.")
            if user_id in user_states:
                del user_states[user_id]
            return
        
        media_type = user_data["media_type"]
        media_path = user_data["media_path"]
        
        if not os.path.exists(media_path):
            bot.reply_to(message, "⚠️ Media file no longer available.")
            del user_data_store[user_id]
            del user_states[user_id]
            return
        
        # Save the media
        safe_name = sanitize_filename(media_name)
        success = save_media(user_id, safe_name, media_path, media_type)
        
        if success:
            bot.reply_to(
                message,
                f"✅ {media_type.capitalize()} saved as '{media_name}'!\n"
                f"You can retrieve it using /my {media_name}"
            )
        else:
            bot.reply_to(message, f"❌ Failed to save the {media_type}. Please try again.")
        
        # Clean up
        del user_data_store[user_id]
        del user_states[user_id]
    
    # Handle cancel command during save
    def cancel_save_handler(message):
        """Cancel the save conversation"""
        user_id = message.from_user.id
        
        # Clean up stored data
        if user_id in user_data_store:
            del user_data_store[user_id]
        
        if user_id in user_states:
            del user_states[user_id]
        
        bot.reply_to(message, "❌ Save operation cancelled.")
    
    # Register a general command handler for /cancel
    @bot.message_handler(commands=['cancel'])
    def general_cancel_command(message):
        """General cancel command handler"""
        user_id = message.from_user.id
        
        if user_id in user_states:
            cancel_save_handler(message)
        else:
            bot.reply_to(message, "No active operation to cancel.")
    
    return bot

def start_bot(bot):
    """Start the bot."""
    # Start the Bot
    bot.infinity_polling()
