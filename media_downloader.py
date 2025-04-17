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
import json
import time
import shutil
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
    # First, normalize the URL if it's shortened
    try:
        if ('vm.tiktok.com' in url.lower() or 
            'vt.tiktok.com' in url.lower() or 
            'www.tiktok.com' not in url.lower()):
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            response = requests.head(url, headers=headers, allow_redirects=True)
            if response.status_code == 200:
                url = response.url
                logger.info(f"Resolved URL to: {url}")
    except Exception as e:
        logger.warning(f"Error following TikTok redirect: {e}")
    
    # Parse the URL
    parsed_url = urllib.parse.urlparse(url)
    if 'tiktok' not in parsed_url.netloc.lower():
        return False
        
    # Check if the URL contains photo indicators
    path = parsed_url.path.lower()
    query = urllib.parse.parse_qs(parsed_url.query)
    
    # Method 1: Check for photo URL pattern (contains /photo/ in path)
    if '/photo/' in path:
        logger.info("Detected TikTok slideshow by path: /photo/")
        return True
    
    # Method 2: Check URL parameters that indicate a slideshow    
    # Check for aweme_type=150 parameter (TikTok photo posts)
    if 'aweme_type' in query and query['aweme_type'][0] == '150':
        logger.info("Detected TikTok slideshow by aweme_type=150")
        return True
        
    # Check for pic_cnt parameter which indicates multiple photos
    if 'pic_cnt' in query:
        try:
            if query['pic_cnt'][0] != '0':
                pic_count = int(query['pic_cnt'][0])
                if pic_count > 0:
                    logger.info(f"Detected TikTok slideshow by pic_cnt={pic_count}")
                    return True
        except (ValueError, TypeError, IndexError):
            # If pic_cnt is present but not a valid number, it might still be a slideshow
            logger.info("Detected possible TikTok slideshow by non-numeric pic_cnt")
            return True
    
    # Method 3: Check the content of the page for slideshow indicators
    # For URLs that don't have obvious indicators in URL, need to check page content
    try:
        # Let's try to fetch the page content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.tiktok.com/',
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # Check for various indicators in the HTML that suggest it's a slideshow
            html_indicators = [
                'photo-mode', 'photoMode', 
                'photoCarousel', 'photo-carousel',
                'multiImage', 'multi-image',
                'image-poster', 'imagePoster',
                'slideshow', 'slide-show',
                'carousel-container', 'imageContainer',
                'photo_mode', 'photoSwiper',
                'gallery-wrapper'
            ]
            
            for indicator in html_indicators:
                if indicator in response.text:
                    logger.info(f"Detected TikTok slideshow by {indicator} in HTML")
                    return True
            
            # Look for specific HTML structures that indicate a slideshow
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for img tags that could be part of a slideshow
            slideshow_img_count = 0
            for img in soup.find_all('img'):
                # If there are multiple images with similar classes/structure, might be a slideshow
                if 'data-src' in img.attrs or 'carousel' in str(img).lower() or 'slide' in str(img).lower():
                    slideshow_img_count += 1
                    if slideshow_img_count >= 2:  # If we find at least 2 slideshow-like images
                        logger.info("Detected TikTok slideshow by multiple carousel-style images in HTML")
                        return True
            
            # Look for JSON data in scripts that might indicate a slideshow
            for script in soup.find_all('script'):
                if script.string and any(x in script.string for x in ['imageList', 'imageMode', 'images":', 'photoIds']):
                    logger.info("Detected TikTok slideshow by image-related data in script")
                    return True
                    
            # Fallback: If the page has 'photo' in its content multiple times, it might be a slideshow
            if response.text.lower().count('photo') > 5 or response.text.lower().count('image') > 10:
                logger.info("Detected possible TikTok slideshow by frequency of 'photo' or 'image' mentions in HTML")
                return True
                
            # Check for meta tags that might indicate a slideshow
            meta_tags = soup.find_all('meta')
            image_meta_count = 0
            for meta in meta_tags:
                if 'content' in meta.attrs and meta['content'].startswith('http') and 'image' in str(meta).lower():
                    image_meta_count += 1
                    if image_meta_count >= 2:  # If we find at least 2 image-related meta tags
                        logger.info("Detected TikTok slideshow by multiple image meta tags")
                        return True
    except Exception as e:
        logger.warning(f"Error checking TikTok page content: {e}")
    
    # If we reach this point, it's probably a regular video
    return False
    
async def download_tiktok_direct(url):
    """
    Direct method to download TikTok videos without using yt-dlp.
    This is a fallback when other methods fail.
    
    Args:
        url (str): URL of the TikTok video
        
    Returns:
        str: Path to the downloaded video file or None if download fails
    """
    logger.info(f"Attempting direct TikTok download for: {url}")
    
    try:
        # Normalize the URL if it's shortened
        try:
            if 'vm.tiktok.com' in url.lower() or 'vt.tiktok.com' in url.lower():
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                }
                response = requests.head(url, headers=headers, allow_redirects=True)
                if response.status_code == 200:
                    url = response.url
                    logger.info(f"Resolved shortened URL to: {url}")
        except Exception as e:
            logger.warning(f"Error following TikTok redirect: {e}")
        
        # Multiple APIs for TikTok video download
        apis = [
            {
                'name': 'snaptik',
                'url': 'https://snaptik.app/api/ajaxSearch',
                'method': 'POST',
                'data': {'url': url},
                'pattern': r'(https:\/\/[^"\']+\.mp4[^"\']*)(?="|\')(?!.*watermark)'
            },
            {
                'name': 'tikmate',
                'url': 'https://tikmate.app/api/lookup',
                'method': 'POST',
                'data': {'url': url},
                'pattern': r'(https:\/\/tikmate\.app\/download\/\w+\.mp4)(?="|\')(?!.*watermark)'
            },
            {
                'name': 'ssstik',
                'url': 'https://ssstik.io/abc?url=dl',
                'method': 'POST',
                'data': {'id': url, 'locale': 'en', 'tt': 'azbjzm'},
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': 'https://ssstik.io',
                    'Referer': 'https://ssstik.io/en'
                },
                'pattern': r'href="(https:\/\/[^"\']+\.mp4[^"\']*)(?="|\')(?!.*watermark)'
            }
        ]
        
        for api in apis:
            try:
                logger.info(f"Trying {api['name']} API for TikTok direct download...")
                headers = api.get('headers', {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                })
                
                if api['method'] == 'POST':
                    response = requests.post(api['url'], data=api['data'], headers=headers, timeout=30)
                else:
                    response = requests.get(api['url'], params=api['data'], headers=headers, timeout=30)
                
                if response.status_code == 200:
                    # Search for download URL in response
                    import re
                    matches = re.findall(api['pattern'], response.text)
                    if matches:
                        download_url = matches[0]
                        logger.info(f"Found direct download URL via {api['name']} API: {download_url}")
                        
                        # Download the video
                        import time
                        timestamp = int(time.time())
                        output_path = os.path.join(DOWNLOAD_DIR, f"tiktok_direct_{timestamp}.mp4")
                        
                        # Use a streaming download to handle large files
                        with requests.get(download_url, stream=True, headers=headers, timeout=60) as dl_response:
                            dl_response.raise_for_status()
                            with open(output_path, 'wb') as f:
                                for chunk in dl_response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                        
                        logger.info(f"Successfully downloaded TikTok video directly to {output_path}")
                        return output_path
            except Exception as e:
                logger.warning(f"Error using {api['name']} API: {e}")
                continue
        
        # If all APIs fail, try downloading directly from the TikTok page
        try:
            logger.info("Trying direct extraction from TikTok page...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Look for video URLs in the page
                video_patterns = [
                    r'(https:\/\/[^"\'\s]+\.mp4[^"\'\s]*)(?=[\s"\'<])',
                    r'playAddr":"(https:\/\/[^"]+\.mp4[^"]*)"',
                    r'playAddr:[ ]*"([^"]+)"',
                    r'"video":[ ]*{"id":"[^"]+","url":"([^"]+)"',
                ]
                
                for pattern in video_patterns:
                    matches = re.findall(pattern, response.text)
                    if matches:
                        for match in matches:
                            try:
                                download_url = match.replace('\\u002F', '/').replace('\\/', '/')
                                logger.info(f"Found direct video URL in TikTok page: {download_url}")
                                
                                # Download the video
                                import time
                                timestamp = int(time.time())
                                output_path = os.path.join(DOWNLOAD_DIR, f"tiktok_page_{timestamp}.mp4")
                                
                                # Use a streaming download to handle large files
                                with requests.get(download_url, stream=True, headers=headers, timeout=60) as dl_response:
                                    if dl_response.status_code == 200:
                                        with open(output_path, 'wb') as f:
                                            for chunk in dl_response.iter_content(chunk_size=8192):
                                                f.write(chunk)
                                        
                                        if os.path.getsize(output_path) > 10000:  # Make sure it's not an empty or tiny file
                                            logger.info(f"Successfully downloaded TikTok video from page to {output_path}")
                                            return output_path
                            except Exception as e:
                                logger.warning(f"Error downloading from extracted URL: {e}")
                                continue
        except Exception as e:
            logger.warning(f"Error during direct page extraction: {e}")
        
        logger.error("All direct TikTok download methods failed")
        return None
        
    except Exception as e:
        logger.error(f"Error in direct TikTok download: {e}")
        return None

async def download_tiktok_slideshow(url):
    """
    Download a TikTok slideshow (photo post).
    Instead of creating a video, this function now extracts and returns all individual images 
    plus audio (if available) separately.
    
    Args:
        url (str): URL of the TikTok slideshow
        
    Returns:
        dict: Dictionary with 'images' (list of paths to image files) and 'audio' (path to audio file or None)
              Returns None if download fails completely
    """
    logger.info(f"Downloading TikTok slideshow from: {url}")
    
    try:
        import requests
        import shutil
        from PIL import Image
        import time
        import re
        
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
            'sec-ch-ua-platform': '"Windows"',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # Normalize the URL if it's shortened
        try:
            if ('vm.tiktok.com' in url.lower() or 
                'vt.tiktok.com' in url.lower()):
                response = requests.head(url, headers=headers, allow_redirects=True)
                if response.status_code == 200:
                    url = response.url
                    logger.info(f"Resolved shortened URL to: {url}")
        except Exception as e:
            logger.warning(f"Error following TikTok redirect: {e}")
        
        # Fetch the TikTok page to extract image URLs and audio URL
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch TikTok page: {response.status_code}")
            return None
            
        # Add debug output to analyze page content
        logger.info(f"Got TikTok page response, length: {len(response.text)} bytes")
        
        # Check for keywords in page content to verify it's a slideshow
        slideshow_indicators = ['/photo/', 'photo-mode', 'photoMode', 'carousel', 'slide', 'gallery']
        found_indicator = None
        for indicator in slideshow_indicators:
            if indicator in response.text:
                found_indicator = indicator
                logger.info(f"Confirmed TikTok slideshow by finding '{indicator}' in page content")
                break
                
        if not found_indicator:
            logger.warning("No slideshow indicators found in page content - might not be a slideshow")
            # Continue anyway as we might still find images
            
        # Parse the HTML to extract image URLs and audio URL
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple methods to extract image URLs from the page
        image_urls = []
        
        # Method 1: Extract from meta tags
        for meta in soup.find_all('meta', property='og:image'):
            if 'content' in meta.attrs and meta['content'] not in image_urls:
                image_urls.append(meta['content'])
                logger.info(f"Found image URL in meta tag: {meta['content']}")
        
        # Method 2: Try to extract from JSON data embedded in the page
        for script in soup.find_all('script'):
            if script.string:
                # Look for various patterns in TikTok's JavaScript data
                patterns = [
                    'window.__INIT_PROPS__', 
                    'window.SIGI_STATE', 
                    'window.__NEXT_DATA__',
                    '"images":', 
                    '"imageList":', 
                    '"imagePostInfo":'
                ]
                
                for pattern in patterns:
                    if pattern in script.string:
                        try:
                            import json
                            import re
                            
                            # Try to find JSON data in the script
                            json_matches = re.findall(r'(\{.*\})', script.string)
                            for json_text in json_matches:
                                try:
                                    data = json.loads(json_text)
                                    
                                    # Search for image URLs in the JSON structure
                                    def extract_image_urls(obj, found_urls=None):
                                        if found_urls is None:
                                            found_urls = []
                                        
                                        if isinstance(obj, dict):
                                            # Check for common keys that might contain image URLs
                                            for key in ['images', 'imageList', 'imagePostInfo', 'imageUrl', 'displayImage', 'thumbnailUrl']:
                                                if key in obj and isinstance(obj[key], list):
                                                    for item in obj[key]:
                                                        if isinstance(item, str) and item.startswith('http') and 'image' in item.lower():
                                                            if item not in found_urls:
                                                                found_urls.append(item)
                                                                logger.info(f"Found image URL in JSON data (list): {item}")
                                                elif key in obj and isinstance(obj[key], str) and obj[key].startswith('http'):
                                                    if obj[key] not in found_urls:
                                                        found_urls.append(obj[key])
                                                        logger.info(f"Found image URL in JSON data (string): {obj[key]}")
                                            
                                            # Recursively search in all dictionary values
                                            for value in obj.values():
                                                extract_image_urls(value, found_urls)
                                        
                                        elif isinstance(obj, list):
                                            # Recursively search in all list items
                                            for item in obj:
                                                extract_image_urls(item, found_urls)
                                        
                                        return found_urls
                                    
                                    # Extract image URLs from JSON
                                    found_urls = extract_image_urls(data)
                                    for url in found_urls:
                                        if url not in image_urls:
                                            image_urls.append(url)
                                except:
                                    # Skip invalid JSON
                                    pass
                        except Exception as e:
                            logger.warning(f"Failed to parse JSON data: {e}")
        
        # Method 3: Look for image URLs in srcset attributes
        for img in soup.find_all('img'):
            if 'src' in img.attrs and img['src'].startswith('http'):
                if img['src'] not in image_urls:
                    image_urls.append(img['src'])
                    logger.info(f"Found image URL in img src: {img['src']}")
            
            if 'srcset' in img.attrs:
                # Parse the srcset attribute which contains multiple URL-size pairs
                srcset_urls = img['srcset'].split(',')
                for srcset_url in srcset_urls:
                    parts = srcset_url.strip().split(' ')
                    if parts and parts[0].startswith('http'):
                        if parts[0] not in image_urls:
                            image_urls.append(parts[0])
                            logger.info(f"Found image URL in srcset: {parts[0]}")
        
        # Method 4: Look for urls in background-image styles
        for element in soup.find_all(style=True):
            style = element['style']
            if 'background-image' in style and 'url(' in style:
                matches = re.findall(r'url\([\'"]?(.*?)[\'"]?\)', style)
                for match in matches:
                    if match.startswith('http') and match not in image_urls:
                        image_urls.append(match)
                        logger.info(f"Found image URL in background-image: {match}")
        
        # If we still don't have images, try a more aggressive approach
        if not image_urls:
            logger.info("No images found with initial methods, trying more aggressive approach")
            
            # Special TikTok image patterns - they don't always use clear .jpg extensions in URLs
            tiktok_image_patterns = [
                r'(https?://[^"\'>\s]+\.image[^"\'>\s]*)',
                r'(https?://[^"\'>\s]+\.tiktokcdn[^"\'>\s]*)',
                r'(https://[^"\'>\s]+\.tiktok\.com/[^"\'>\s]+)',
                r'property="og:image"\s+content="([^"]+)"',
                r'<img[^>]+src="([^"]+)"',
                r'"image":"([^"]+)"',
                r'"images":\s*\[\s*"([^"]+)"',
                r'"imageList":\s*\[\s*"([^"]+)"',
                r'"imagePostInfo":[^{]*"url":"([^"]+)"',
                r'"originCover":"([^"]+)"',
                r'"thumbnailUrl":"([^"]+)"',
                r'"imageUrl":"([^"]+)"',
                r'"animatedCoverUrl":"([^"]+)"'
            ]
            
            for pattern in tiktok_image_patterns:
                try:
                    matches = re.findall(pattern, response.text)
                    for match in matches:
                        image_url = match
                        if isinstance(match, tuple) and len(match) > 0:
                            image_url = match[0]
                        
                        # Clean up the URL - TikTok often has escaped URLs
                        image_url = image_url.replace('\\u002F', '/').replace('\\/', '/').replace('\\', '')
                        
                        # Add https:// if it's missing
                        if image_url.startswith('//'):
                            image_url = 'https:' + image_url
                            
                        # Only add if it looks like a valid image URL
                        if image_url.startswith('http') and (
                                'image' in image_url.lower() or 
                                'tiktok' in image_url.lower() or 
                                any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp'])):
                            if image_url not in image_urls:
                                image_urls.append(image_url)
                                logger.info(f"Found image URL with pattern {pattern}: {image_url}")
                            
                    # If we've found at least 2 images, that's probably good enough
                    if len(image_urls) >= 2:
                        logger.info(f"Found {len(image_urls)} image URLs, proceeding with download")
                        break
                except Exception as e:
                    logger.warning(f"Error extracting image URLs with pattern {pattern}: {e}")
            
            # If still no images, try the generic approach
            if not image_urls:
                try:
                    url_pattern = r'(https?://[^\s\'"\)]+\.(jpg|jpeg|png|webp))'
                    matches = re.findall(url_pattern, response.text)
                    for match in matches:
                        full_url = match[0]  # Get the full URL from the match
                        if full_url not in image_urls:
                            image_urls.append(full_url)
                            logger.info(f"Found image URL with generic regex: {full_url}")
                except Exception as e:
                    logger.warning(f"Error extracting image URLs with generic regex: {e}")
                    
            # Fallback extraction method - use a direct approach when nothing else works
            if not image_urls:
                logger.info("No images found with regex methods, trying direct API extraction")
                try:
                    # Extract the item_id from the URL which is needed for the API
                    item_id = None
                    item_id_pattern = r'photo/(\d+)'
                    item_id_match = re.search(item_id_pattern, url)
                    if item_id_match:
                        item_id = item_id_match.group(1)
                    
                    # If we have an item_id, we can try the direct TikTok API approach
                    if item_id:
                        logger.info(f"Found item_id: {item_id}, trying direct API")
                        # This is a fallback approach using TikTok's public API
                        api_url = f"https://api.tiktok.com/aweme/v1/multi/aweme/detail/?aweme_ids=%5B{item_id}%5D"
                        api_headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Referer': 'https://www.tiktok.com/',
                            'Accept': 'application/json'
                        }
                        api_response = requests.get(api_url, headers=api_headers)
                        if api_response.status_code == 200:
                            try:
                                data = api_response.json()
                                # Recursively search for image URLs in the API response
                                if 'aweme_details' in data and data['aweme_details']:
                                    for detail in data['aweme_details']:
                                        if 'image_post_info' in detail and detail['image_post_info']:
                                            images_data = detail['image_post_info'].get('images', [])
                                            for img in images_data:
                                                if 'display_image' in img and img['display_image']:
                                                    image_url = img['display_image'].get('url_list', [])[0]
                                                    if image_url and image_url not in image_urls:
                                                        image_urls.append(image_url)
                                                        logger.info(f"Found image URL from API: {image_url}")
                            except Exception as e:
                                logger.warning(f"Error parsing TikTok API response: {e}")
                except Exception as e:
                    logger.warning(f"Error with direct API extraction: {e}")
        
        # Extract audio URL - try multiple methods
        audio_url = None
        # Method 1: Check meta tags
        for meta in soup.find_all('meta', property='og:audio'):
            if 'content' in meta.attrs:
                audio_url = meta['content']
                logger.info(f"Found audio URL in meta tag: {audio_url}")
                break
        
        # Method 2: Look for audio tags
        if not audio_url:
            for audio in soup.find_all('audio'):
                if 'src' in audio.attrs and audio['src'].startswith('http'):
                    audio_url = audio['src']
                    logger.info(f"Found audio URL in audio tag: {audio_url}")
                    break
        
        # Method 3: Look for audio URLs in the page source
        if not audio_url:
            audio_patterns = [
                r'(https?://[^\s\'"\)]+\.(mp3|m4a|aac|wav))',
                r'"musicUrl"\s*:\s*"([^"]+)"',
                r'"audioUrl"\s*:\s*"([^"]+)"',
                r'"audio_url"\s*:\s*"([^"]+)"',
                r'"music":[^}]*"playUrl"\s*:\s*"([^"]+)"',
                r'"audio":[^}]*"url"\s*:\s*"([^"]+)"',
                r'"soundtrack":[^}]*"url"\s*:\s*"([^"]+)"'
            ]
            for pattern in audio_patterns:
                matches = re.findall(pattern, response.text)
                if matches:
                    if isinstance(matches[0], tuple):
                        # If the match is a tuple (from the URL pattern), get the full URL
                        audio_url = matches[0][0]
                    else:
                        # For other patterns that capture just the URL in a group
                        audio_url = matches[0]
                    logger.info(f"Found audio URL with regex: {audio_url}")
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
        
        # Return the images and audio without creating a video
        if not image_paths:
            logger.error("No images were successfully downloaded")
            return None
            
        # Now instead of creating a video, return the individual files
        logger.info(f"Successfully downloaded {len(image_paths)} images and audio: {audio_path is not None}")
        
        result = {
            'images': image_paths,
            'audio': audio_path
        }
        
        return result
        
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
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # For TikTok URLs, perform more robust detection of slideshows
        if 'tiktok' in domain:
            # Special handling for obvious slideshow URLs first - don't even attempt video download
            if '/photo/' in parsed_url.path.lower() or 'aweme_type=150' in url:
                logger.info("URL contains explicit slideshow indicators, using slideshow downloader directly")
                slideshow_result = await download_tiktok_slideshow(url)
                if slideshow_result:
                    logger.info("Successfully downloaded TikTok slideshow")
                    return {'type': 'slideshow', 'data': slideshow_result}
                logger.error("Direct slideshow download failed")
                return None
                
            # For less obvious cases, perform additional detection
            try:
                is_slideshow = await is_tiktok_slideshow(url)
                if is_slideshow:
                    logger.info("Detected TikTok slideshow, trying dedicated slideshow downloader")
                    slideshow_result = await download_tiktok_slideshow(url)
                    if slideshow_result and isinstance(slideshow_result, dict):
                        # Return dictionary with images and audio for separate handling by the bot
                        return {'type': 'slideshow', 'data': slideshow_result}
                    logger.warning("Slideshow download failed, falling back to regular video download")
            except Exception as e:
                logger.error(f"Error in TikTok slideshow detection: {e}, continuing with regular video download")
        
        # Determine platform-specific options
        options = YDL_OPTIONS.copy()
        
        # Update options with better settings for reliability
        options.update({
            'socket_timeout': 60,  # Increased timeout
            'retries': 5,          # More retries
            'fragment_retries': 10, # For segmented downloads
            'overwrites': True     # Overwrite existing files
        })
        
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
            
            # Try a more reliable approach for TikTok - use multiple APIs and browser simulation
            options.update({
                # Enhanced options for TikTok
                'extractor_retries': 5,  # Increase retry attempts
                'socket_timeout': 60,    # Increase timeout for slow connections
                'extractor_args': {
                    'tiktok': {
                        'embed_api': ['tiktokv', 'ssstik', 'tikwm', 'tikmate'],  # Try multiple API endpoints
                        'api_hostname': 'tikmate.app',  # More reliable service
                        'force_api_response': 'yes',
                        'force_mobile_api': 'yes'  # Try mobile API which might be more reliable
                    }
                },
                'referer': 'https://www.tiktok.com/',
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"'
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
        
        # If TikTok download failed, try multiple fallback methods
        if (not video_path or not os.path.exists(video_path)) and 'tiktok' in domain:
            logger.info("Initial TikTok download failed, trying first fallback method...")
            
            # Try first fallback method with a different API
            options['extractor_args']['tiktok'] = {
                'embed_api': 'musicaldown',
                'api_hostname': 'musicaldown.com',
                'force_mobile_api': 'yes'
            }
            
            video_path = await loop.run_in_executor(None, download)
            
            # If first fallback fails, try a direct request method (bypass yt-dlp)
            if not video_path or not os.path.exists(video_path):
                logger.info("Second fallback: Trying direct download method for TikTok...")
                try:
                    # Simple implementation to avoid any dependency issues
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept': '*/*',
                        'Referer': 'https://www.tiktok.com/',
                    }
                    
                    # Try to get the video page
                    response = requests.get(url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        # Look for video URLs in the page
                        video_pattern = r'(https://[^"\']+\.mp4[^"\']*)'
                        matches = re.findall(video_pattern, response.text)
                        
                        for match in matches:
                            try:
                                video_url = match.replace('\\u002F', '/').replace('\\/', '/')
                                logger.info(f"Found direct video URL: {video_url}")
                                
                                # Download the video
                                timestamp = int(time.time())
                                output_path = os.path.join(DOWNLOAD_DIR, f"tiktok_fallback_{timestamp}.mp4")
                                
                                with requests.get(video_url, stream=True, headers=headers, timeout=60) as dl_response:
                                    if dl_response.status_code == 200:
                                        with open(output_path, 'wb') as f:
                                            for chunk in dl_response.iter_content(chunk_size=8192):
                                                f.write(chunk)
                                        
                                        if os.path.getsize(output_path) > 10000:  # Check file is not empty
                                            logger.info(f"Successfully downloaded TikTok video directly: {output_path}")
                                            video_path = output_path
                                            break
                            except Exception as e:
                                logger.warning(f"Error downloading from found URL: {e}")
                
                except Exception as e:
                    logger.error(f"Error in direct TikTok download: {e}")
            
            # Last resort - try with a completely different method using a different API
            if not video_path or not os.path.exists(video_path):
                logger.info("Third fallback: Trying TikTok download with SaveFrom API...")
                try:
                    savefrom_url = f"https://en.savefrom.net/download-from-tiktok/#url={url}"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Referer': 'https://www.google.com/'
                    }
                    
                    response = requests.get(savefrom_url, headers=headers)
                    if response.status_code == 200:
                        video_pattern = r'(https://[^"\']+\.mp4[^"\']*)'
                        matches = re.findall(video_pattern, response.text)
                        
                        for match in matches:
                            try:
                                timestamp = int(time.time())
                                output_path = os.path.join(DOWNLOAD_DIR, f"tiktok_savefrom_{timestamp}.mp4")
                                
                                with requests.get(match, stream=True, headers=headers, timeout=60) as dl_response:
                                    if dl_response.status_code == 200:
                                        with open(output_path, 'wb') as f:
                                            for chunk in dl_response.iter_content(chunk_size=8192):
                                                f.write(chunk)
                                                
                                        if os.path.getsize(output_path) > 10000:
                                            logger.info(f"Successfully downloaded TikTok video with SaveFrom: {output_path}")
                                            video_path = output_path
                                            break
                            except Exception as e:
                                logger.warning(f"Error with SaveFrom API download: {e}")
                                continue
                except Exception as e:
                    logger.error(f"Error in SaveFrom TikTok download: {e}")
                    
        if not video_path or not os.path.exists(video_path):
            logger.error(f"Download failed for {url}")
            return None
        
        logger.info(f"Successfully downloaded video to {video_path}")
        return video_path
    
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return None
