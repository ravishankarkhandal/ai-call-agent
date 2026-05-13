# transcriber.py
import requests
import tempfile
import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from twilio.rest import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Validate environment variables
api_key = os.getenv("OPENAI_API_KEY")
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

if not api_key:
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY environment variable is required")

if not account_sid or not auth_token:
    logger.error("TWILIO credentials not found in environment variables")
    raise ValueError("Twilio credentials are required")

try:
    openai_client = OpenAI(api_key=api_key)
    twilio_client = Client(account_sid, auth_token)
except Exception as e:
    logger.error(f"Failed to initialize clients: {e}")
    raise

def transcribe_recording(recording_url: str, language: str = "hi") -> str:
    """Twilio recording URL se audio download karo aur text mein convert karo"""
    
    tmp_path = None
    
    try:
        # Validate URL
        if not recording_url or not isinstance(recording_url, str):
            logger.error(f"Invalid recording URL: {recording_url}")
            return "Recording URL invalid hai."
        
        logger.info(f"Starting transcription for: {recording_url}")
        
        # Recording download karo (authentication ke saath)
        auth = (account_sid, auth_token)
        
        # Ensure URL has correct format
        if not recording_url.endswith(".mp3"):
            recording_url = recording_url + ".mp3"
        
        audio_response = requests.get(
            recording_url, 
            auth=auth,
            timeout=30
        )
        
        if audio_response.status_code != 200:
            logger.error(f"Recording download failed (Status: {audio_response.status_code})")
            return f"Recording download nahi hui (Status: {audio_response.status_code})"
        
        if len(audio_response.content) == 0:
            logger.error("Downloaded recording is empty")
            return "Recording empty hai."
        
        logger.info(f"Recording downloaded successfully ({len(audio_response.content)} bytes)")
        
        # Temporary file mein save karo
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_file.write(audio_response.content)
            tmp_path = tmp_file.name
            logger.info(f"Temporary file created at: {tmp_path}")
        
        # Validate language parameter
        valid_languages = ["hi", "en", "ta", "te", "ml", "kn"]
        if language not in valid_languages:
            logger.warning(f"Invalid language {language}, defaulting to 'hi'")
            language = "hi"
        
        # OpenAI Whisper se transcribe karo
        logger.info(f"Starting transcription with language: {language}")
        
        with open(tmp_path, "rb") as audio_file:
            transcription = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                timeout=60
            )
        
        text = transcription.text
        logger.info(f"Transcription completed: {len(text)} characters")
        
        return text if text else "Transcription khaali hai (koi awaaz capture nahi hui)."
        
    except requests.Timeout:
        logger.error("Request timeout while downloading recording")
        return "Recording download timeout. Try again."
    
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return f"Recording access error: {str(e)[:100]}"
    
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        return f"Transcription fail hui: {str(e)[:100]}"
    
    finally:
        # Temp file delete karo safely
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
                logger.info(f"Temporary file deleted: {tmp_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")