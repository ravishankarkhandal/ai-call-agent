# summarizer.py
from openai import OpenAI
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY environment variable is required")

try:
    client = OpenAI(api_key=api_key)
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    raise

def summarize_call(transcript: str, caller_number: str) -> str:
    """Transcript ki concise summary banata hai"""
    
    try:
        # Validate inputs
        if not transcript or not isinstance(transcript, str):
            logger.warning("Empty or invalid transcript provided")
            return "Call mein koi meaningful conversation nahi hui."
        
        transcript = transcript.strip()
        
        # Check minimum length
        if len(transcript) < 10:
            logger.warning("Transcript too short to summarize")
            return "Call bahut chhota tha, kuch detail capture nahi hui."
        
        # Limit transcript length to prevent API issues
        max_transcript_length = 5000
        if len(transcript) > max_transcript_length:
            transcript = transcript[:max_transcript_length]
            logger.warning(f"Transcript truncated to {max_transcript_length} characters")
        
        # Validate caller_number
        if not caller_number:
            caller_number = "Unknown"
        
        prompt = f"""Ek phone call ki transcript hai jisme ek AI agent ne mere behalf pe call li.
Caller ka number: {caller_number}

Transcript:
{transcript}

Mujhe iska concise summary do (100-200 words):
1. Caller kaun tha / kya kaam tha
2. Kya information li/di gayi
3. Koi important action item hai toh batao
4. Summary Hindi ya English mein de sakte ho

Summary:
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Aap ek helpful assistant ho jo phone call summaries banate ho. Concise aur to-the-point jawab dena."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.5,
            timeout=15
        )
        
        summary = response.choices[0].message.content
        logger.info("Summary generated successfully")
        return summary
    
    except Exception as e:
        logger.error(f"Error in summarize_call: {e}", exc_info=True)
        # Return fallback summary
        if transcript:
            return f"Call summary: {transcript[:200]}..."
        return "Summary generate nahi ho saki. Technical issue aayi."