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
        'vm.tiktok.com',
        'instagram.com',
        'youtube.com',
        'youtu.be',
        'pinterest.com',
        'pin.it'
    ]
    
    # Check if the URL is from a supported domain
    for supported in supported_domains:
        if supported in domain:
            return True
    
    return False

def get_url_type(url):
    """
    Determine the type of URL (video or image) and the platform.
    
    Args:
        url (str): URL to check
        
    Returns:
        tuple: (type, platform) where type is 'video' or 'image' and platform is the social media platform
    """
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc.lower()
    path = parsed_url.path.lower()
    
    # Pinterest
    if 'pinterest' in domain or 'pin.it' in domain:
        from pinterest_extractor import is_pinterest_video_url
        if is_pinterest_video_url(url):
            return ('video', 'pinterest')
        # Otherwise assume it's an image
        return ('image', 'pinterest')
    
    # Instagram
    elif 'instagram' in domain:
        if '/reel/' in path or '/reels/' in path:
            return ('video', 'instagram')
        return ('video', 'instagram')  # Default to video for Instagram (most use case)
    
    # TikTok is always video
    elif 'tiktok' in domain:
        return ('video', 'tiktok')
    
    # YouTube is always video
    elif 'youtube' in domain or 'youtu.be' in domain:
        return ('video', 'youtube')
    
    # Default to video for any other supported platform
    return ('video', 'unknown')

def get_media_type(file_path):
    """
    Determine the media type based on file extension.
    
    Args:
        file_path (str): Path to the media file
        
    Returns:
        str: 'video', 'audio', or 'image' based on the file extension
    """
    if not file_path:
        return None
    
    ext = os.path.splitext(file_path)[1].lower()
    
    video_extensions = ['.mp4', '.avi', '.mov', '.flv', '.wmv', '.mkv', '.webm']
    audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac']
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
    
    if ext in video_extensions:
        return 'video'
    elif ext in audio_extensions:
        return 'audio'
    elif ext in image_extensions:
        return 'image'
    else:
        # Try to guess based on the file path
        if 'image' in file_path.lower() or 'photo' in file_path.lower() or 'pinterest' in file_path.lower():
            return 'image'
        # Default to video for truly unknown extensions
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
