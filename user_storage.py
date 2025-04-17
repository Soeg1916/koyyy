"""
User storage module for managing user-specific media files.
"""
import os
import json
import shutil
import logging
from pathlib import Path
from utils import sanitize_filename

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define storage directory
STORAGE_BASE_DIR = os.path.join(os.path.expanduser("~"), ".social_media_bot")
STORAGE_DATA_FILE = os.path.join(STORAGE_BASE_DIR, "user_data.json")

def initialize_user_storage():
    """Initialize the storage directories and data file."""
    os.makedirs(STORAGE_BASE_DIR, exist_ok=True)
    
    # Create the data file if it doesn't exist
    if not os.path.exists(STORAGE_DATA_FILE):
        with open(STORAGE_DATA_FILE, 'w') as f:
            json.dump({}, f)
        logger.info("Initialized user storage data file")

def _get_user_data():
    """Get the user data from the JSON file."""
    try:
        with open(STORAGE_DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        logger.warning("User data file not found or corrupted, creating new one")
        with open(STORAGE_DATA_FILE, 'w') as f:
            json.dump({}, f)
        return {}

def _save_user_data(data):
    """Save the user data to the JSON file."""
    with open(STORAGE_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def _get_user_dir(user_id):
    """Get the storage directory for a specific user."""
    user_dir = os.path.join(STORAGE_BASE_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def save_media(user_id, name, source_path, media_type):
    """
    Save a media file for a specific user.
    
    Args:
        user_id (int): Telegram user ID
        name (str): Name to save the media as
        source_path (str): Path to the source media file
        media_type (str): Type of media (video or audio)
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        # Ensure the name is valid and safe
        safe_name = sanitize_filename(name)
        
        # Determine file extension
        ext = os.path.splitext(source_path)[1]
        if not ext:
            ext = ".mp4" if media_type == "video" else ".mp3"
        
        # Create filename
        filename = f"{safe_name}{ext}"
        
        # Get user directory
        user_dir = _get_user_dir(user_id)
        
        # Create destination path
        dest_path = os.path.join(user_dir, filename)
        
        # Copy the file
        shutil.copy2(source_path, dest_path)
        
        # Update user data
        user_data = _get_user_data()
        
        # Initialize user data if not exists
        if str(user_id) not in user_data:
            user_data[str(user_id)] = {}
        
        # Save file information
        user_data[str(user_id)][safe_name] = {
            "path": filename,
            "type": media_type
        }
        
        # Save user data
        _save_user_data(user_data)
        
        logger.info(f"Saved {media_type} as '{safe_name}' for user {user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving media: {str(e)}")
        return False

def retrieve_media(user_id, name):
    """
    Retrieve a saved media file.
    
    Args:
        user_id (int): Telegram user ID
        name (str): Name of the saved media
        
    Returns:
        tuple: (file_path, media_type) if found, None otherwise
    """
    try:
        # Get user data
        user_data = _get_user_data()
        
        # Check if user exists
        if str(user_id) not in user_data:
            logger.warning(f"No data found for user {user_id}")
            return None
        
        # Check if the media name exists
        user_media = user_data[str(user_id)]
        
        # Try to find the media by exact name or case-insensitive match
        media_info = None
        name_lower = name.lower()
        
        if name in user_media:
            media_info = user_media[name]
        else:
            # Try case-insensitive search
            for saved_name, info in user_media.items():
                if saved_name.lower() == name_lower:
                    media_info = info
                    break
        
        if not media_info:
            logger.warning(f"Media '{name}' not found for user {user_id}")
            return None
        
        # Get file path
        user_dir = _get_user_dir(user_id)
        file_path = os.path.join(user_dir, media_info["path"])
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"File {file_path} not found")
            return None
        
        return (file_path, media_info["type"])
    
    except Exception as e:
        logger.error(f"Error retrieving media: {str(e)}")
        return None

def get_user_media_list(user_id):
    """
    Get a list of saved media for a user.
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        list: List of tuples (name, type) of saved media
    """
    try:
        # Get user data
        user_data = _get_user_data()
        
        # Check if user exists
        if str(user_id) not in user_data:
            return []
        
        # Get user media
        user_media = user_data[str(user_id)]
        
        # Return list of (name, type) tuples
        return [(name, info["type"]) for name, info in user_media.items()]
    
    except Exception as e:
        logger.error(f"Error getting user media list: {str(e)}")
        return []

def delete_media(user_id, name):
    """
    Delete a saved media file for a specific user.
    
    Args:
        user_id (int): Telegram user ID
        name (str): Name of the saved media to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        # Get user data
        user_data = _get_user_data()
        
        # Check if user exists
        if str(user_id) not in user_data:
            logger.warning(f"No data found for user {user_id}")
            return False
        
        # Check if the media name exists
        user_media = user_data[str(user_id)]
        found_name = None
        
        # Try to find the media by exact name or case-insensitive match
        name_lower = name.lower()
        
        if name in user_media:
            found_name = name
        else:
            # Try case-insensitive search
            for saved_name in user_media.keys():
                if saved_name.lower() == name_lower:
                    found_name = saved_name
                    break
        
        if not found_name:
            logger.warning(f"Media '{name}' not found for user {user_id}")
            return False
        
        # Get file path
        media_info = user_media[found_name]
        user_dir = _get_user_dir(user_id)
        file_path = os.path.join(user_dir, media_info["path"])
        
        # Delete the file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
        else:
            logger.warning(f"File not found: {file_path}")
        
        # Remove the entry from user data
        del user_data[str(user_id)][found_name]
        _save_user_data(user_data)
        
        logger.info(f"Deleted media '{found_name}' for user {user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error deleting media: {str(e)}")
        return False
