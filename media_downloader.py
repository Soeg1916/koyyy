"""
Media downloader for various social media platforms.
Handles downloading videos from TikTok, Instagram, YouTube Shorts, and Pinterest.
Also supports downloading images from Pinterest and TikTok slideshows.
"""
import os
import logging
import asyncio
import urllib.parse
import tempfile
import yt_dlp
import re
import requests
from bs4 import BeautifulSoup
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

async def is_tiktok_slideshow(url):
    """
    Check if the TikTok URL is a slideshow (photo post) rather than a video.
    
    Args:
        url (str): TikTok URL to check
        
    Returns:
        bool: True if it's a slideshow, False otherwise
    """
    parsed_url = urllib.parse.urlparse(url)
    if 'tiktok' not in parsed_url.netloc.lower():
        return False
        
    # Check if the URL contains photo indicators
    path = parsed_url.path.lower()
    query = urllib.parse.parse_qs(parsed_url.query)
    
    # Check for photo URL pattern (contains /photo/ in path)
    if '/photo/' in path:
        return True
        
    # Check for aweme_type=150 parameter (TikTok photo posts)
    if 'aweme_type' in query and query['aweme_type'][0] == '150':
        return True
        
    # Check for pic_cnt parameter which indicates multiple photos
    if 'pic_cnt' in query and int(query['pic_cnt'][0]) > 0:
        return True
        
    return False
    
async def download_tiktok_slideshow(url):
    """
    Download a TikTok slideshow (photo post) and convert it to a video with audio.
    
    Args:
        url (str): URL of the TikTok slideshow
        
    Returns:
        str: Path to the created slideshow video or None if download fails
    """
    logger.info(f"Downloading TikTok slideshow from: {url}")
    
    try:
        from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
        import requests
        import shutil
        from PIL import Image
        import time
        
        # Create a unique directory for this slideshow
        timestamp = int(time.time())
        slideshow_dir = os.path.join(DOWNLOAD_DIR, f"tiktok_slideshow_{timestamp}")
        os.makedirs(slideshow_dir, exist_ok=True)
        
        # Get cookies and headers to access TikTok content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.tiktok.com/',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        # Fetch the TikTok page to extract image URLs and audio URL
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch TikTok page: {response.status_code}")
            return None
            
        # Parse the HTML to extract image URLs and audio URL
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to extract image URLs from JSON data embedded in the page
        json_data = None
        for script in soup.find_all('script'):
            if script.string and 'window.__INIT_PROPS__' in script.string:
                try:
                    import json
                    start_idx = script.string.find('{')
                    end_idx = script.string.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_text = script.string[start_idx:end_idx]
                        json_data = json.loads(json_text)
                        break
                except Exception as e:
                    logger.warning(f"Failed to parse JSON data: {e}")
        
        # Extract image URLs from meta tags if JSON extraction failed
        image_urls = []
        if not json_data:
            for meta in soup.find_all('meta', property='og:image'):
                if 'content' in meta.attrs:
                    image_urls.append(meta['content'])
        
        # Extract audio URL
        audio_url = None
        for meta in soup.find_all('meta', property='og:audio'):
            if 'content' in meta.attrs:
                audio_url = meta['content']
                break
                
        if not image_urls:
            logger.error("Failed to extract image URLs from TikTok page")
            return None
            
        # Download images
        image_paths = []
        for i, img_url in enumerate(image_urls):
            try:
                img_path = os.path.join(slideshow_dir, f"image_{i}.jpg")
                img_response = requests.get(img_url, headers=headers, stream=True)
                if img_response.status_code == 200:
                    with open(img_path, 'wb') as f:
                        img_response.raw.decode_content = True
                        shutil.copyfileobj(img_response.raw, f)
                    image_paths.append(img_path)
                    logger.info(f"Downloaded image {i+1}/{len(image_urls)}")
                else:
                    logger.warning(f"Failed to download image {i+1}: {img_response.status_code}")
            except Exception as e:
                logger.warning(f"Error downloading image {i+1}: {e}")
        
        # Download audio if available
        audio_path = None
        if audio_url:
            try:
                audio_path = os.path.join(slideshow_dir, "audio.mp3")
                audio_response = requests.get(audio_url, headers=headers, stream=True)
                if audio_response.status_code == 200:
                    with open(audio_path, 'wb') as f:
                        audio_response.raw.decode_content = True
                        shutil.copyfileobj(audio_response.raw, f)
                    logger.info("Downloaded audio track")
                else:
                    logger.warning(f"Failed to download audio: {audio_response.status_code}")
                    audio_path = None
            except Exception as e:
                logger.warning(f"Error downloading audio: {e}")
                audio_path = None
        
        # Create a video slideshow from the images
        if not image_paths:
            logger.error("No images were successfully downloaded")
            return None
            
        # Create a video slideshow with the images
        # Each image will be shown for 3 seconds
        clips = []
        for img_path in image_paths:
            try:
                clip = ImageClip(img_path).set_duration(3)
                clips.append(clip)
            except Exception as e:
                logger.warning(f"Error creating clip from image {img_path}: {e}")
        
        if not clips:
            logger.error("Failed to create any video clips from images")
            return None
        
        # Combine the clips into a single video
        video_clip = concatenate_videoclips(clips, method="compose")
        
        # Add audio if available
        if audio_path and os.path.exists(audio_path):
            try:
                audio_clip = AudioFileClip(audio_path)
                # Loop the audio if it's shorter than the video
                if audio_clip.duration < video_clip.duration:
                    audio_clip = audio_clip.loop(duration=video_clip.duration)
                # Trim the audio if it's longer than the video
                elif audio_clip.duration > video_clip.duration:
                    audio_clip = audio_clip.subclip(0, video_clip.duration)
                video_clip = video_clip.set_audio(audio_clip)
            except Exception as e:
                logger.warning(f"Error adding audio to video: {e}")
        
        # Save the final video
        output_path = os.path.join(DOWNLOAD_DIR, f"tiktok_slideshow_{timestamp}.mp4")
        video_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
        
        # Clean up
        video_clip.close()
        shutil.rmtree(slideshow_dir, ignore_errors=True)
        
        logger.info(f"Successfully created TikTok slideshow video at {output_path}")
        return output_path
        
    except ImportError as e:
        logger.error(f"Required library missing: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating TikTok slideshow video: {e}")
        return None

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
        # First, check if this is a TikTok slideshow (image carousel)
        if await is_tiktok_slideshow(url):
            logger.info("Detected TikTok slideshow")
            return await download_tiktok_slideshow(url)
        
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
