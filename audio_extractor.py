"""
Audio extractor module to extract audio from video files using ffmpeg.
"""
import os
import logging
import asyncio
import tempfile
import subprocess
from pathlib import Path

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create a directory for extracted audio if it doesn't exist
AUDIO_DIR = os.path.join(tempfile.gettempdir(), "extracted_audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

async def extract_audio(video_path):
    """
    Extract audio from a video file.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        str: Path to the extracted audio file or None if extraction fails
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return None
    
    try:
        # Generate output path for audio
        video_filename = os.path.basename(video_path)
        base_name = os.path.splitext(video_filename)[0]
        audio_path = os.path.join(AUDIO_DIR, f"{base_name}.mp3")
        
        logger.info(f"Extracting audio from {video_path} to {audio_path}")
        
        # Define ffmpeg command
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-q:a", "0",  # Best quality
            "-map", "a",  # Only extract audio
            "-y",  # Overwrite output files without asking
            audio_path
        ]
        
        # Create a function to run ffmpeg in a subprocess
        def run_ffmpeg():
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    logger.error(f"FFmpeg error: {stderr.decode()}")
                    return None
                
                if not os.path.exists(audio_path):
                    logger.error("Audio extraction failed: Output file not created")
                    return None
                
                return audio_path
            except Exception as e:
                logger.error(f"Error in FFmpeg subprocess: {str(e)}")
                return None
        
        # Run ffmpeg in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_ffmpeg)
        
        if result:
            logger.info(f"Audio extraction successful: {audio_path}")
            return audio_path
        else:
            logger.error("Audio extraction failed")
            return None
        
    except Exception as e:
        logger.error(f"Error extracting audio: {str(e)}")
        return None
