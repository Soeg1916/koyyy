"""
User storage module for managing user-specific media files.
Vercel-compatible version that uses in-memory storage for serverless environment.
"""
import os
import json
import logging
import time
from utils import sanitize_filename

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# In-memory storage for Vercel (serverless environment)
# Note: Data will be lost when function instance is recycled
USER_DATA = {}
TEMP_STORAGE = {}  # { user_id: { name: (content, media_type, timestamp) } }

# Define a temp directory that works in Vercel
TEMP_DIR = "/tmp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR, exist_ok=True)

def initialize_user_storage():
    """Initialize the storage for Vercel."""
    logger.info("Initialized in-memory user storage for Vercel")
    # Nothing to initialize in the serverless version - we're using in-memory storage

def _get_user_data():
    """Get the user data from in-memory storage."""
    global USER_DATA
    return USER_DATA.copy()

def _save_user_data(data):
    """Save the user data to in-memory storage."""
    global USER_DATA
    USER_DATA = data.copy()

def _get_user_dir(user_id):
    """
    Get the temporary storage directory for a specific user.
    Each user has their own directory based on their Telegram ID.
    For Vercel, we use the /tmp directory which is writable.
    """
    # Ensure user_id is converted to string and sanitized
    safe_user_id = str(user_id).replace('..', '').replace('/', '').replace('\\', '')
    user_dir = os.path.join(TEMP_DIR, f"telegram_bot_{safe_user_id}")
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def save_media(user_id, name, source_path, media_type):
    """
    Save a media file for a specific user (in-memory for Vercel).
    
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
        
        # For Vercel, we don't persist files between invocations
        # Instead, we'll keep track of the relationship in memory
        user_data = _get_user_data()
        
        # Initialize user data if not exists
        if str(user_id) not in user_data:
            user_data[str(user_id)] = {}
        
        # Save file information - we only track names for webhook responses
        user_data[str(user_id)][safe_name] = {
            "name": safe_name,
            "type": media_type,
            "added": int(time.time())
        }
        
        # Save user data
        _save_user_data(user_data)
        
        logger.info(f"Saved reference to {media_type} as '{safe_name}' for user {user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving media: {str(e)}")
        return False

def retrieve_media(user_id, name):
    """
    Retrieve a saved media reference.
    Note: On Vercel, this will only check if the name exists in the user's saved list,
    but the actual file might not be available anymore.
    
    Args:
        user_id (int): Telegram user ID
        name (str): Name of the saved media
        
    Returns:
        tuple: (None, media_type) if reference found, None otherwise
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
        
        # For Vercel, we can't guarantee the file is still available
        # Return the media type but no file path
        logger.info(f"Found reference to media '{name}' for user {user_id}")
        
        # Instead, tell the user that persistent storage is not supported
        return (None, media_info["type"])
    
    except Exception as e:
        logger.error(f"Error retrieving media: {str(e)}")
        return None

def get_user_media_list(user_id):
    """
    Get a list of saved media references for a user.
    
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
    Delete a saved media reference for a specific user.
    
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
        
        # Remove the entry from user data
        del user_data[str(user_id)][found_name]
        _save_user_data(user_data)
        
        logger.info(f"Deleted media reference '{found_name}' for user {user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error deleting media: {str(e)}")
        return False