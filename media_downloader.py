"""
Media downloader for various social media platforms.
Handles downloading videos from TikTok, Instagram, YouTube Shorts, and Pinterest.
"""
import os
import logging
import asyncio
import urllib.parse
import tempfile
import yt_dlp
from utils import sanitize_filename

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create a downloads directory if it doesn't exist
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "social_media_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Configure yt-dlp options
YDL_OPTIONS = {
    'format': 'best',
    'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'ignoreerrors': True,
    'nocheckcertificate': True,
    'restrictfilenames': True,
    'logtostderr': False,
    'verbose': False,
}

async def download_video(url):
    """
    Download video from supported social media platforms.
    
    Args:
        url (str): URL of the video to download
        
    Returns:
        str: Path to the downloaded video file or None if download fails
    """
    logger.info(f"Downloading video from: {url}")
    
    try:
        # Determine platform-specific options
        options = YDL_OPTIONS.copy()
        
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc.lower()
        
        if 'tiktok' in domain:
            logger.info("Detected TikTok URL")
            options.update({
                'cookiesfrombrowser': ('chrome',),  # Extract cookies from browser
            })
            
        elif 'instagram' in domain:
            logger.info("Detected Instagram URL")
            options.update({
                'cookiesfrombrowser': ('chrome',),  # Extract cookies from browser
            })
            
        elif 'youtube' in domain or 'youtu.be' in domain:
            logger.info("Detected YouTube URL")
            # No special options needed, yt-dlp handles YouTube well by default
            
        elif 'pinterest' in domain:
            logger.info("Detected Pinterest URL")
            options.update({
                'cookiesfrombrowser': ('chrome',),  # Extract cookies from browser
            })
            
        # Generate a unique filename based on timestamp to prevent conflicts
        import time
        timestamp = int(time.time())
        temp_filename = f"video_{timestamp}"
        options['outtmpl'] = os.path.join(DOWNLOAD_DIR, f"{temp_filename}.%(ext)s")
        
        # Download the video using yt-dlp in a separate process
        def download():
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    return None
                
                if 'entries' in info:
                    # Playlist or compilation video - take the first one
                    info = info['entries'][0]
                
                # Get the actual filename
                for key in ['requested_downloads', '_filename']:
                    if key in info and info[key]:
                        if key == 'requested_downloads':
                            return info[key][0]['filepath']
                        return info[key]
                        
                # Fallback - construct filename from template and extension
                filename = f"{temp_filename}.{info.get('ext', 'mp4')}"
                return os.path.join(DOWNLOAD_DIR, filename)
        
        # Run the download in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        video_path = await loop.run_in_executor(None, download)
        
        if not video_path or not os.path.exists(video_path):
            logger.error(f"Download failed for {url}")
            return None
        
        logger.info(f"Successfully downloaded video to {video_path}")
        return video_path
    
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return None
