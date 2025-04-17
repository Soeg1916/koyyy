"""
Utility functions for the Telegram bot.
"""
import re
import os
import tempfile
import logging
import urllib.parse

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_valid_url(text):
    """
    Check if a text contains a valid URL from supported platforms.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text contains a valid URL, False otherwise
    """
    # Simple URL regex pattern
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    
    # Check if text contains a URL
    match = re.search(url_pattern, text)
    if not match:
        return False
    
    url = match.group(0)
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc.lower()
    
    # List of supported domains
    supported_domains = [
        'tiktok.com',
        'instagram.com',
        'youtube.com',
        'youtu.be',
        'pinterest.com'
    ]
    
    # Check if the URL is from a supported domain
    for supported in supported_domains:
        if supported in domain:
            return True
    
    return False

def get_media_type(file_path):
    """
    Determine the media type based on file extension.
    
    Args:
        file_path (str): Path to the media file
        
    Returns:
        str: 'video' or 'audio' based on the file extension
    """
    if not file_path:
        return None
    
    ext = os.path.splitext(file_path)[1].lower()
    
    video_extensions = ['.mp4', '.avi', '.mov', '.flv', '.wmv', '.mkv', '.webm']
    audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac']
    
    if ext in video_extensions:
        return 'video'
    elif ext in audio_extensions:
        return 'audio'
    else:
        # Default to video for unknown extensions
        return 'video'

def sanitize_filename(filename):
    """
    Sanitize a filename to make it safe for all file systems.
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Limit length to avoid file system limits
    max_length = 50
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Trim spaces from start and end
    sanitized = sanitized.strip()
    
    # If after sanitization the name is empty, give it a default name
    if not sanitized:
        sanitized = "media_file"
    
    return sanitized

def create_temp_dir():
    """
    Create a temporary directory for storing downloads.
    
    Returns:
        str: Path to the temporary directory
    """
    temp_dir = os.path.join(tempfile.gettempdir(), "telegram_bot_downloads")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir
