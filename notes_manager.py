# notes_manager.py
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NOTES_DIR = "notes"
NOTES_FILE = os.path.join(NOTES_DIR, "call_notes.md")

def save_note(caller_number: str, summary: str, transcript: str) -> str:
    """Call ki summary notes file mein save karta hai"""
    
    try:
        # Validate inputs
        if not caller_number or not isinstance(caller_number, str):
            caller_number = "Unknown"
        
        if not summary or not isinstance(summary, str):
            summary = "No summary available"
        
        if not transcript or not isinstance(transcript, str):
            transcript = "No transcript available"
        
        # Sanitize inputs
        caller_number = caller_number.strip()[:50]  # Limit length
        summary = summary.strip()
        transcript = transcript.strip()
        
        # Notes folder banao agar na ho
        try:
            os.makedirs(NOTES_DIR, exist_ok=True)
            logger.info(f"Notes directory ensured: {NOTES_DIR}")
        except OSError as e:
            logger.error(f"Failed to create notes directory: {e}")
            raise
        
        # Current date aur time
        now = datetime.now().strftime("%d %B %Y, %I:%M %p")
        
        # Note ka format with proper markdown
        note_entry = f"""---
## 📞 Call — {now}
**Caller:** {caller_number}

### Summary
{summary}

### Full Transcript
{transcript}

---

"""
        
        # File mein append karo (purani notes delete na hon)
        try:
            with open(NOTES_FILE, "a", encoding="utf-8") as f:
                f.write(note_entry)
            
            logger.info(f"✅ Note saved: {NOTES_FILE}")
            return NOTES_FILE
        
        except IOError as e:
            logger.error(f"Failed to write to notes file: {e}")
            # Try alternate location
            alt_file = os.path.join(NOTES_DIR, f"call_notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
            try:
                with open(alt_file, "w", encoding="utf-8") as f:
                    f.write(note_entry)
                logger.warning(f"Saved to alternate file: {alt_file}")
                return alt_file
            except Exception as e2:
                logger.error(f"Failed to save to alternate file: {e2}")
                raise
    
    except Exception as e:
        logger.error(f"Error in save_note: {e}", exc_info=True)
        raise