"""
Pinterest image extractor module.
Handles downloading images from Pinterest pins.
"""
import os
import re
import logging
import tempfile
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create a downloads directory if it doesn't exist
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "pinterest_images")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def download_pinterest_image(url):
    """
    Download image from Pinterest.
    
    Args:
        url (str): URL of the Pinterest pin
        
    Returns:
        str: Path to the downloaded image file or None if download fails
    """
    logger.info(f"Downloading Pinterest image from: {url}")
    
    try:
        # Set up headers to simulate a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.pinterest.com/'
        }
        
        # Normalize Pinterest URL if needed
        if 'pin.it' in url:
            logger.info("Converting shortened Pinterest URL to full URL")
            try:
                response = requests.head(url, headers=headers, allow_redirects=True)
                if response.status_code == 200:
                    url = response.url
                    logger.info(f"Resolved to: {url}")
            except Exception as e:
                logger.warning(f"Error following Pinterest redirect: {e}")
        
        # Fetch the Pinterest page
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch Pinterest page: {response.status_code}")
            return None
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the image URL - Pinterest stores high-res images in meta tags
        image_url = None
        
        # Method 1: Look for og:image meta tag (most reliable)
        try:
            og_image = soup.find('meta', property='og:image')
            if og_image and hasattr(og_image, 'attrs') and 'content' in og_image.attrs:
                image_url = og_image.attrs['content']
                logger.info(f"Found image URL in og:image meta tag: {image_url}")
        except (AttributeError, TypeError):
            logger.warning("Error accessing og:image meta tag properties")
        
        # Method 2: Look for high-res image tags
        if not image_url:
            images = soup.find_all('img')
            # Filter for Pinterest images and sort by size if available
            pinterest_images = []
            for img in images:
                src = img.get('src')
                if src and ('pinimg.com' in src or 'pinterest.com' in src):
                    # Check for dimensions in the URL or attributes
                    width = img.get('width')
                    if width:
                        try:
                            width = int(width)
                            pinterest_images.append((src, width))
                        except ValueError:
                            pinterest_images.append((src, 0))
                    else:
                        # Try to find dimensions in the URL
                        size_match = re.search(r'(\d+)x(\d+)', src)
                        if size_match:
                            width = int(size_match.group(1))
                            pinterest_images.append((src, width))
                        else:
                            pinterest_images.append((src, 0))
            
            # Sort by size (largest first)
            if pinterest_images:
                pinterest_images.sort(key=lambda x: x[1], reverse=True)
                image_url = pinterest_images[0][0]
                logger.info(f"Found image in sorted list: {image_url}")
        
        # Method 3: Look for data-test-id attributes (Pinterest's UI elements)
        if not image_url:
            image_elements = soup.find_all(attrs={"data-test-id": "pin-closeup-image"})
            for element in image_elements:
                img = element.find('img')
                if img and img.get('src'):
                    image_url = img.get('src')
                    logger.info(f"Found image with data-test-id: {image_url}")
                    break
        
        # If we couldn't find an image URL, return None
        if not image_url:
            logger.error("Could not find image URL on Pinterest page")
            return None
        
        # Download the image
        if not isinstance(image_url, str):
            logger.error("Invalid image URL type")
            return None
            
        image_response = requests.get(image_url, headers=headers)
        if image_response.status_code != 200:
            logger.error(f"Failed to download image: {image_response.status_code}")
            return None
        
        # Determine the file extension
        content_type = image_response.headers.get('content-type', '').lower()
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = 'jpg'
        elif 'png' in content_type:
            ext = 'png'
        elif 'gif' in content_type:
            ext = 'gif'
        elif 'webp' in content_type:
            ext = 'webp'
        else:
            # Default to jpg if we can't determine the type
            ext = 'jpg'
        
        # Generate a filename
        import time
        timestamp = int(time.time())
        filename = f"pinterest_image_{timestamp}.{ext}"
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        
        # Save the image
        with open(file_path, 'wb') as f:
            f.write(image_response.content)
        
        logger.info(f"Successfully downloaded Pinterest image to {file_path}")
        return file_path
    
    except Exception as e:
        logger.error(f"Error downloading Pinterest image: {str(e)}")
        return None

async def download_pinterest_video(url):
    """
    Download video from Pinterest.
    
    Args:
        url (str): URL of the Pinterest pin with video
        
    Returns:
        str: Path to the downloaded video file or None if download fails
    """
    logger.info(f"Downloading Pinterest video from: {url}")
    
    try:
        # Set up headers to simulate a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://www.pinterest.com/'
        }
        
        # Normalize Pinterest URL if needed
        if 'pin.it' in url:
            logger.info("Converting shortened Pinterest URL to full URL")
            try:
                response = requests.head(url, headers=headers, allow_redirects=True)
                if response.status_code == 200:
                    url = response.url
                    logger.info(f"Resolved to: {url}")
            except Exception as e:
                logger.warning(f"Error following Pinterest redirect: {e}")
        
        # Fetch the Pinterest page
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch Pinterest page: {response.status_code}")
            return None
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the video URL - Pinterest stores video URLs in multiple places
        video_url = None
        
        # Method 1: Look for og:video meta tag
        try:
            og_video = soup.find('meta', property='og:video')
            if og_video and hasattr(og_video, 'attrs') and 'content' in og_video.attrs:
                video_url = og_video.attrs['content']
                logger.info(f"Found video URL in og:video meta tag: {video_url}")
        except (AttributeError, TypeError):
            logger.warning("Error accessing og:video meta tag properties")
            
        # Method 2: Look for og:video:url meta tag
        if not video_url:
            try:
                og_video_url = soup.find('meta', property='og:video:url')
                if og_video_url and hasattr(og_video_url, 'attrs') and 'content' in og_video_url.attrs:
                    video_url = og_video_url.attrs['content']
                    logger.info(f"Found video URL in og:video:url meta tag: {video_url}")
            except (AttributeError, TypeError):
                logger.warning("Error accessing og:video:url meta tag properties")
        
        # Method 3: Look for video tags
        if not video_url:
            video_tags = soup.find_all('video')
            for video_tag in video_tags:
                src = video_tag.get('src')
                if src:
                    video_url = src
                    logger.info(f"Found video source in video tag: {video_url}")
                    break
                
                # Check for source tags inside video
                source_tags = video_tag.find_all('source')
                for source in source_tags:
                    src = source.get('src')
                    if src:
                        video_url = src
                        logger.info(f"Found video source in source tag: {video_url}")
                        break
        
        # Method 4: Look for data in JSON-LD scripts
        if not video_url:
            scripts = soup.find_all('script', attrs={'type': 'application/ld+json'})
            for script in scripts:
                if script.string:
                    try:
                        import json
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'video' in data and 'contentUrl' in data['video']:
                            video_url = data['video']['contentUrl']
                            logger.info(f"Found video URL in JSON-LD: {video_url}")
                            break
                    except (json.JSONDecodeError, KeyError, TypeError):
                        continue
        
        # Method 5: Look for video URL in Redux state
        if not video_url:
            scripts = soup.find_all('script', attrs={'type': 'application/json'})
            for script in scripts:
                if script.string and '"videos"' in script.string:
                    try:
                        import json
                        data = json.loads(script.string)
                        if 'props' in data and 'initialReduxState' in data['props']:
                            pins = data['props']['initialReduxState'].get('pins', {})
                            if pins:
                                pin_id = list(pins.keys())[0]
                                pin_data = pins[pin_id]
                                if 'videos' in pin_data and pin_data['videos'].get('video_list'):
                                    videos = pin_data['videos']['video_list']
                                    # Find the highest quality video
                                    best_video = None
                                    best_quality = 0
                                    for video_id, video_info in videos.items():
                                        quality = int(video_info.get('width', 0))
                                        if quality > best_quality and 'url' in video_info:
                                            best_quality = quality
                                            best_video = video_info['url']
                                    
                                    if best_video:
                                        video_url = best_video
                                        logger.info(f"Found video URL in Redux state: {video_url}")
                    except Exception as e:
                        logger.warning(f"Error parsing JSON data for video: {e}")
        
        # If we couldn't find a video URL, return None
        if not video_url:
            logger.error("Could not find video URL on Pinterest page")
            return None
        
        # Check if it's actually a valid video URL (not just an image)
        if 'jpg' in video_url or 'jpeg' in video_url or 'png' in video_url or 'webp' in video_url or 'gif' in video_url:
            logger.error("Found image URL instead of video URL")
            return None
        
        # Download the video
        if not isinstance(video_url, str):
            logger.error("Invalid video URL type")
            return None
            
        video_response = requests.get(video_url, headers=headers, stream=True)
        if video_response.status_code != 200:
            logger.error(f"Failed to download video: {video_response.status_code}")
            return None
        
        # Check if the content type is a video type
        content_type = video_response.headers.get('content-type', '').lower()
        if not ('video' in content_type or 'octet-stream' in content_type):
            logger.error(f"Content is not a video: {content_type}")
            return None
        
        # Determine the file extension from content type or URL
        if 'mp4' in video_url.lower():
            ext = 'mp4'
        elif 'webm' in video_url.lower():
            ext = 'webm'
        elif 'mov' in video_url.lower():
            ext = 'mov'
        else:
            # Default to mp4 if we can't determine the type
            ext = 'mp4'
        
        # Generate a filename
        import time
        timestamp = int(time.time())
        filename = f"pinterest_video_{timestamp}.{ext}"
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        
        # Save the video
        with open(file_path, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Successfully downloaded Pinterest video to {file_path}")
        return file_path
    
    except Exception as e:
        logger.error(f"Error downloading Pinterest video: {str(e)}")
        return None

def is_pinterest_video_url(url):
    """
    Check if a URL is likely to be a Pinterest video rather than an image.
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: True if it's likely a Pinterest video URL, False otherwise
    """
    parsed_url = urlparse(url)
    
    # Pinterest domains
    if 'pinterest' not in parsed_url.netloc and 'pin.it' not in parsed_url.netloc:
        return False
    
    # Check for video-specific paths/parameters
    path = parsed_url.path.lower()
    
    # Pinterest video pins often have these indicators in the URL
    video_indicators = ['/video/', 'watch/', 'player/', 'reel/']
    for indicator in video_indicators:
        if indicator in path:
            return True
    
    return False