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
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
    'noplaylist': True,
    'quiet': False,  # Set to False to see more debugging info
    'no_warnings': False,  # Set to False to see warnings
    'ignoreerrors': False,  # Set to False to see errors
    'nocheckcertificate': True,
    'restrictfilenames': True,
    'logtostderr': True,  # Log to stderr for debugging
    'verbose': True,  # Enable verbose output for debugging
    'socket_timeout': 30,  # Increase timeout
    'retries': 10,  # Increase number of retries
    'cachedir': False,  # Disable cache
    'prefer_insecure': True,  # Try HTTP if HTTPS fails
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    },
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
        
        # Special handling for TikTok
        if 'tiktok' in domain:
            logger.info("Detected TikTok URL")
            
            # Normalize TikTok URL if it's a shortened one (vm.tiktok.com)
            if 'vm.tiktok.com' in domain:
                logger.info("Converting shortened TikTok URL to full URL")
                try:
                    import requests
                    response = requests.head(url, allow_redirects=True)
                    if response.status_code == 200:
                        url = response.url
                        logger.info(f"Resolved to: {url}")
                        # Re-parse the URL after redirection
                        parsed_url = urllib.parse.urlparse(url)
                except Exception as e:
                    logger.warning(f"Error following TikTok redirect: {e}")
            
            # Try a different approach for TikTok - use browser simulation
            options.update({
                # Use an alternative extractor
                'extractor_retries': 3,
                'extractor_args': {
                    'tiktok': {
                        'embed_api': 'tikwm',  # Try different API endpoints
                        'api_hostname': 'www.tikwm.com',
                        'force_api_response': 'yes'
                    }
                },
                'referer': 'https://www.tiktok.com/',
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            })
            
        elif 'instagram' in domain:
            logger.info("Detected Instagram URL")
            options.update({
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.instagram.com/'
                }
            })
            
        elif 'youtube' in domain or 'youtu.be' in domain:
            logger.info("Detected YouTube URL")
            # No special options needed, yt-dlp handles YouTube well by default
            
        elif 'pinterest' in domain:
            logger.info("Detected Pinterest URL")
            options.update({
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.pinterest.com/'
                }
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
        
        # If TikTok download failed, try a fallback method
        if (not video_path or not os.path.exists(video_path)) and 'tiktok' in domain:
            logger.info("Initial TikTok download failed, trying fallback method...")
            
            # Try fallback method with a different API
            options['extractor_args']['tiktok'] = {
                'embed_api': 'musicaldown',
                'api_hostname': 'musicaldown.com',
                'force_mobile_api': 'yes'
            }
            
            video_path = await loop.run_in_executor(None, download)
        
        if not video_path or not os.path.exists(video_path):
            logger.error(f"Download failed for {url}")
            return None
        
        logger.info(f"Successfully downloaded video to {video_path}")
        return video_path
    
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return None
