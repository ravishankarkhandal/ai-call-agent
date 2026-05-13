# ai_handler.py
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

# Conversation history store karne ke liye (simple in-memory)
conversations = {}

SYSTEM_PROMPT = """Aap ek professional AI assistant ho jo apne owner ke behalf pe phone calls handle karte ho.

Aapka naam "Assistant" hai. Owner abhi busy hai.

Guidelines:
- Professionally baat karo (Hindi ya English dono mein)
- Caller ka naam aur kaam zaroor poochho
- Important information note karo (kab call back karein, kya kaam hai)
- Politely baat karo
- Call zyada lamba mat karo - 2-3 minutes mein khatam karo
- Agar emergency ho toh owner ko message karne ka suggest karo

Shuru mein ye bolna: "Hello! Main [owner] ke AI assistant hoon. Abhi woh busy hain. Main aapka message note kar sakta hoon. Aap kaun bol rahe hain aur aapka kya kaam tha?"
"""

def get_ai_response(session_id: str, user_message: str) -> str:
    """AI se response lo"""
    
    try:
        # Validate inputs
        if not session_id or not isinstance(session_id, str):
            logger.warning(f"Invalid session_id: {session_id}")
            return "Technical error. Please try again."
        
        if not user_message or not isinstance(user_message, str):
            logger.warning(f"Invalid user_message: {user_message}")
            return "Main aapki awaaz sun nahi paaya. Dobara baat karein."
        
        # Conversation history initialize karo
        if session_id not in conversations:
            conversations[session_id] = []
        
        # User message add karo
        conversations[session_id].append({
            "role": "user",
            "content": user_message[:500]  # Limit message length to prevent issues
        })
        
        # Keep conversation history limited to last 10 messages
        if len(conversations[session_id]) > 20:
            conversations[session_id] = conversations[session_id][-20:]
        
        # OpenAI se response lo
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *conversations[session_id]
            ],
            max_tokens=150,
            temperature=0.7,
            timeout=10
        )
        
        ai_reply = response.choices[0].message.content
        
        # AI response bhi history mein save karo
        conversations[session_id].append({
            "role": "assistant", 
            "content": ai_reply
        })
        
        logger.info(f"AI response generated for session {session_id}")
        return ai_reply
    
    except Exception as e:
        logger.error(f"Error in get_ai_response: {e}", exc_info=True)
        return "Maafi chahta hoon, kuch technical issue aayi. Baad mein try karein."

def get_full_conversation(session_id: str) -> str:
    """Poori conversation text mein do"""
    
    try:
        if not session_id or session_id not in conversations:
            logger.warning(f"No conversation found for session {session_id}")
            return ""
        
        transcript_lines = []
        for msg in conversations[session_id]:
            role = "Caller" if msg["role"] == "user" else "AI Agent"
            transcript_lines.append(f"{role}: {msg['content']}")
        
        return "\n".join(transcript_lines)
    
    except Exception as e:
        logger.error(f"Error in get_full_conversation: {e}")
        return ""

def clear_conversation(session_id: str):
    """Session khatam hone pe conversation clear karo"""
    try:
        if session_id in conversations:
            del conversations[session_id]
            logger.info(f"Conversation cleared for session {session_id}")
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")