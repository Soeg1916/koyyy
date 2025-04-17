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
from pinterest_extractor import download_pinterest_image, download_pinterest_video
from user_storage import (
    save_media,
    retrieve_media,
    get_user_media_list,
    delete_media,
    initialize_user_storage,
)
from utils import is_valid_url, get_media_type, get_url_type, sanitize_filename

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store temporary user data
user_data_store = {}

# Store recently downloaded media with user_id as key and a list of media paths as value
# This is a cache of media files that users might want to extract audio from or save
media_cache = {}

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
            "I can help you download videos and images from social media platforms, extract audio, and save your media.\n\n"
            "Just send me a link to a video from TikTok, Instagram, YouTube Shorts, or Pinterest, or a link to a photo from Pinterest.\n\n"
            "Commands:\n"
            "/help - Show help information\n"
            "/list - List your saved media\n"
            "/my [name] - Retrieve your saved media by name\n"
            "/delete [name] - Delete your saved media by name"
        )
        bot.reply_to(message, welcome_message)
    
    @bot.message_handler(commands=['help'])
    def help_command(message):
        """Handler for /help command"""
        help_message = (
            "📋 Bot Instructions:\n\n"
            "1️⃣ Send a link to a video from TikTok, Instagram, YouTube Shorts, or Pinterest\n"
            "   OR send a link to a Pinterest image\n"
            "2️⃣ I'll download and send you the video or image\n"
            "3️⃣ For videos: Use the '🎵 Download Audio' button to extract audio\n"
            "4️⃣ Use the '💾 Save' button to save any media with a custom name\n"
            "5️⃣ Use /list to see all your saved media (🎬 videos, 🎵 audio, 🖼️ images)\n"
            "6️⃣ Use /my [name] to retrieve your saved media\n"
            "7️⃣ Use /delete [name] to delete your saved media\n\n"
            "Examples:\n"
            "• To retrieve: /my my_favorite_image\n"
            "• To delete: /delete my_favorite_image"
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
            if media_type == "audio":
                icon = "🎵"
            elif media_type == "image":
                icon = "🖼️"
            else:
                icon = "🎬"
            response += f"{i}. {icon} {name}\n"
        
        response += "\nTo retrieve a file, use /my [name]"
        response += "\nTo delete a file, use /delete [name]"
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
        elif media_type == "image":
            with open(file_path, 'rb') as image_file:
                bot.send_photo(message.chat.id, image_file, caption=f"Your saved image: {media_name}")
    
    @bot.message_handler(commands=['delete'])
    def delete_command(message):
        """Handler for /delete [name] command"""
        user_id = message.from_user.id
        command_args = message.text.split(' ', 1)
        
        if len(command_args) < 2:
            bot.reply_to(message, "Please provide a name. Usage: /delete [name]")
            return
        
        media_name = command_args[1].strip()
        success = delete_media(user_id, media_name)
        
        if success:
            bot.reply_to(message, f"✅ Media '{media_name}' has been deleted successfully.")
        else:
            bot.reply_to(message, f"❌ No media found with the name '{media_name}' or deletion failed.")
    
    @bot.message_handler(func=lambda message: is_valid_url(message.text))
    def handle_url_message(message):
        """Handler for messages containing URLs"""
        url = message.text
        user_id = message.from_user.id
        
        # Determine the media type (video or image)
        media_type, platform = get_url_type(url)
        logger.info(f"Detected URL type: {media_type} from {platform}")
        
        # Check if this is a group chat
        is_group = message.chat.type in ['group', 'supergroup']
        
        # In group chats, only process messages from specific platforms
        if is_group and platform not in ['tiktok', 'instagram', 'pinterest']:
            logger.info(f"Ignoring URL in group chat: platform {platform} not supported for groups")
            return
            
        # Let the user know we're working on it
        status_message = bot.send_message(message.chat.id, "🔄 Processing your request. This may take a moment...")
        
        # Use a thread to handle the download process
        def download_thread():
            try:
                # Initialize variables
                download_result = None
                
                # Determine which download function to use based on the media type
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                if platform == 'pinterest':
                    if media_type == 'image':
                        # Download Pinterest image
                        download_result = loop.run_until_complete(download_pinterest_image(url))
                        if download_result:
                            logger.info(f"Downloaded Pinterest image to {download_result}")
                    else:
                        # Download Pinterest video
                        download_result = loop.run_until_complete(download_pinterest_video(url))
                        if download_result:
                            logger.info(f"Downloaded Pinterest video to {download_result}")
                elif platform == 'tiktok' and media_type == 'slideshow':
                    # For TikTok slideshows, use the dedicated slideshow download function
                    from media_downloader import download_tiktok_slideshow
                    logger.info("Using dedicated TikTok slideshow downloader")
                    slideshow_result = loop.run_until_complete(download_tiktok_slideshow(url))
                    if slideshow_result:
                        download_result = {'type': 'slideshow', 'data': slideshow_result}
                        logger.info(f"Downloaded TikTok slideshow as separate images and audio")
                    else:
                        logger.error("TikTok slideshow download failed")
                        bot.edit_message_text("❌ Failed to download the TikTok slideshow. The content may be private or no longer available.", 
                                           message.chat.id, status_message.message_id)
                        return
                else:
                    # Default to video download for all other platforms
                    download_result = loop.run_until_complete(download_video(url))
                
                if not download_result:
                    error_msg = "❌ Failed to download the media. Please check the URL and try again."
                    bot.edit_message_text(error_msg, message.chat.id, status_message.message_id)
                    return
                    
                # Check if we got a TikTok slideshow result (dictionary with images and audio)
                if isinstance(download_result, dict) and download_result.get('type') == 'slideshow':
                    # Handle TikTok slideshow specially by sending images and audio separately
                    slideshow_data = download_result.get('data', {})
                    image_paths = slideshow_data.get('images', [])
                    audio_path = slideshow_data.get('audio')
                    
                    if not image_paths:
                        bot.edit_message_text("❌ Failed to extract images from the slideshow.", 
                                           message.chat.id, status_message.message_id)
                        return
                    
                    # Inform the user we're sending slideshow content
                    bot.edit_message_text(f"✅ Downloaded TikTok slideshow with {len(image_paths)} images" + 
                                      (" and audio" if audio_path else "") + "! Sending now...", 
                                      message.chat.id, status_message.message_id)
                    
                    # Send each image separately
                    for i, img_path in enumerate(image_paths):
                        try:
                            # Create a unique ID for this image
                            import hashlib
                            import time
                            img_id = hashlib.md5(f"{user_id}_{time.time()}_{img_path}_{i}".encode()).hexdigest()[:10]
                            
                            # Cache the image path
                            if user_id not in media_cache:
                                media_cache[user_id] = {}
                            media_cache[user_id][img_id] = img_path
                            
                            # Create markup for saving the image
                            markup = types.InlineKeyboardMarkup()
                            save_button = types.InlineKeyboardButton("💾 Save Image", 
                                                             callback_data=f"save_image_{img_id}")
                            markup.add(save_button)
                            
                            # Send the image
                            with open(img_path, 'rb') as img_file:
                                caption = f"Slideshow image {i+1}/{len(image_paths)}"
                                bot.send_photo(message.chat.id, img_file, caption=caption, reply_markup=markup)
                        except Exception as e:
                            logger.error(f"Error sending image {i+1}: {e}")
                            bot.send_message(message.chat.id, f"⚠️ Error sending image {i+1}")
                    
                    # Send audio if available
                    if audio_path and os.path.exists(audio_path):
                        try:
                            # Create a unique ID for the audio
                            audio_id = hashlib.md5(f"{user_id}_{time.time()}_audio".encode()).hexdigest()[:10]
                            
                            # Cache the audio path
                            if user_id not in media_cache:
                                media_cache[user_id] = {}
                            media_cache[user_id][audio_id] = audio_path
                            
                            # Create markup for saving the audio
                            markup = types.InlineKeyboardMarkup()
                            save_button = types.InlineKeyboardButton("💾 Save Audio", 
                                                             callback_data=f"save_audio_{audio_id}")
                            markup.add(save_button)
                            
                            # Send the audio
                            with open(audio_path, 'rb') as audio_file:
                                bot.send_audio(message.chat.id, audio_file, 
                                            caption="Slideshow audio track", 
                                            title="TikTok Slideshow Audio",
                                            reply_markup=markup)
                        except Exception as e:
                            logger.error(f"Error sending audio: {e}")
                            bot.send_message(message.chat.id, "⚠️ Error sending audio track")
                    
                    logger.info(f"Sent TikTok slideshow with {len(image_paths)} images and audio: {audio_path is not None}")
                    return
                    
                # For regular media (not slideshow), use the standard approach
                media_path = download_result
                
                if not os.path.exists(media_path):
                    error_msg = "❌ Failed to access the downloaded media file."
                    bot.edit_message_text(error_msg, message.chat.id, status_message.message_id)
                    return
                
                # Generate a unique ID for this media file
                import hashlib
                import time
                media_id = hashlib.md5(f"{user_id}_{time.time()}_{media_path}".encode()).hexdigest()[:10]
                
                # Store the media path in the cache
                if user_id not in media_cache:
                    media_cache[user_id] = {}
                media_cache[user_id][media_id] = media_path
                
                # Create inline keyboard markup
                markup = types.InlineKeyboardMarkup()
                
                if media_type == 'video' or media_type == 'slideshow':
                    # For videos and slideshows, add audio extraction button
                    extract_button = types.InlineKeyboardButton("🎵 Download Audio", 
                                                            callback_data=f"extract_{media_id}")
                    save_button = types.InlineKeyboardButton("💾 Save", 
                                                          callback_data=f"save_video_{media_id}")
                    markup.add(extract_button, save_button)
                else:
                    # For images, just add save button
                    save_button = types.InlineKeyboardButton("💾 Save", 
                                                          callback_data=f"save_image_{media_id}")
                    markup.add(save_button)
                
                # Delete the status message
                bot.delete_message(message.chat.id, status_message.message_id)
                
                # Send the media with appropriate method based on type
                local_media_type = get_media_type(media_path)
                
                if local_media_type == 'video':
                    # Send as video
                    with open(media_path, 'rb') as media_file:
                        bot.send_video(message.chat.id, media_file, caption="Here's your downloaded video!", 
                                      reply_markup=markup)
                
                elif local_media_type == 'image':
                    # Send as photo
                    with open(media_path, 'rb') as media_file:
                        bot.send_photo(message.chat.id, media_file, caption="Here's your downloaded image!", 
                                      reply_markup=markup)
                
                else:
                    # Default handling for other media types
                    with open(media_path, 'rb') as media_file:
                        bot.send_document(message.chat.id, media_file, caption="Here's your downloaded media!", 
                                         reply_markup=markup)
                
                logger.info(f"Cached media ({local_media_type}) with ID {media_id} for user {user_id}")
                
            except Exception as e:
                logger.error(f"Error downloading media: {e}")
                bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, status_message.message_id)
        
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('extract_'))
    def extract_audio_callback(call):
        """Handle callback for extracting audio from a video"""
        bot.answer_callback_query(call.id)
        
        user_id = call.from_user.id
        
        # Get the media ID from the callback data
        media_id = call.data.split("_")[1]
        
        # Check if the user has this media in cache
        if user_id not in media_cache or media_id not in media_cache[user_id]:
            bot.edit_message_caption(caption="⚠️ Video file no longer available. Please download it again.", 
                                   chat_id=call.message.chat.id, 
                                   message_id=call.message.message_id)
            return
        
        # Get the video path from the cache
        video_path = media_cache[user_id][media_id]
        
        # Verify the file still exists
        if not os.path.exists(video_path):
            bot.edit_message_caption(caption="⚠️ Video file no longer available. Please download it again.", 
                                   chat_id=call.message.chat.id, 
                                   message_id=call.message.message_id)
            # Remove from cache since file is gone
            del media_cache[user_id][media_id]
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
                
                # Generate a unique ID for the audio
                import hashlib
                import time
                audio_id = hashlib.md5(f"{user_id}_{time.time()}_{audio_path}".encode()).hexdigest()[:10]
                
                # Add audio to media cache
                media_cache[user_id][audio_id] = audio_path
                
                # Create inline keyboard with save button
                markup = types.InlineKeyboardMarkup()
                save_button = types.InlineKeyboardButton("💾 Save", 
                                                      callback_data=f"save_audio_{audio_id}")
                markup.add(save_button)
                
                # Send the audio file
                with open(audio_path, 'rb') as audio_file:
                    bot.send_audio(call.message.chat.id, audio_file,
                                 caption="Here's the extracted audio!",
                                 reply_markup=markup)
                
                # Restore the original video caption with its buttons
                markup = types.InlineKeyboardMarkup()
                extract_button = types.InlineKeyboardButton("🎵 Download Audio", 
                                                         callback_data=f"extract_{media_id}")
                save_button = types.InlineKeyboardButton("💾 Save", 
                                                      callback_data=f"save_video_{media_id}")
                markup.add(extract_button, save_button)
                
                bot.edit_message_caption(caption="Here's your downloaded video!",
                                       chat_id=call.message.chat.id,
                                       message_id=call.message.message_id,
                                       reply_markup=markup)
                
                logger.info(f"Extracted audio {audio_id} from video {media_id} for user {user_id}")
                
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
        
        _, media_type, media_id = data_parts
        user_id = call.from_user.id
        
        # Check if the user has this media in cache
        if user_id not in media_cache or media_id not in media_cache[user_id]:
            bot.send_message(call.message.chat.id, "⚠️ Media file no longer available. Please download it again.")
            return
        
        # Get the actual file path from the cache
        media_path = media_cache[user_id][media_id]
        
        # Verify the file still exists
        if not os.path.exists(media_path):
            bot.send_message(call.message.chat.id, "⚠️ Media file no longer available. Please download it again.")
            # Remove from cache since file is gone
            del media_cache[user_id][media_id]
            return
        
        # Store data for the conversation
        user_data_store[user_id] = {
            "media_type": media_type,
            "media_path": media_path,
            "media_id": media_id,
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
        if "media_id" in user_data and user_id in media_cache and user_data["media_id"] in media_cache[user_id]:
            # After successful save, we can remove from temporary cache
            logger.info(f"Removing media {user_data['media_id']} from cache after saving as '{media_name}'")
            del media_cache[user_id][user_data["media_id"]]
            
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
