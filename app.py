# app.py
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from dotenv import load_dotenv
import os
import threading
import logging

from ai_handler import get_ai_response, get_full_conversation, clear_conversation
from summarizer import summarize_call
from notes_manager import save_note

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# Validate environment variables
required_env_vars = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "OPENAI_API_KEY", "TWILIO_PHONE_NUMBER"]
for var in required_env_vars:
    if not os.getenv(var):
        logger.warning(f"Warning: {var} not set in environment")

try:
    twilio_client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )
except Exception as e:
    logger.error(f"Twilio client initialization failed: {e}")
    twilio_client = None

# ─────────────────────────────────────────────
# ROUTE 1: Jab call aaye — pehla response
# ─────────────────────────────────────────────
@app.route("/incoming-call", methods=["POST"])
def incoming_call():
    """Twilio isko call aane pe hit karta hai"""
    
    try:
        caller = request.form.get("From", "Unknown")
        call_sid = request.form.get("CallSid", "")
        
        logger.info(f"📞 Call aaya: {caller} (SID: {call_sid})")
        
        # Static first message (proper greeting instead of "CALL_STARTED")
        first_message = "Hello! Main ek AI assistant hoon. Owner abhi busy hain. Aap apna naam aur kaam batayein?"
        
        # Get AI response for continuity
        get_ai_response(call_sid, "Call started - listening to caller")
        
        # TwiML response banao
        response = VoiceResponse()
        
        # Enable recording
        response.record(
            action="/record-callback",
            method="POST",
            timeout=1,
            max_length=3600
        )
        
        # AI bolega aur phir caller ki baat sunne ke liye Gather use karein
        gather = Gather(
            input="speech",           # Voice input lo
            action="/handle-speech",  # Jawab ke baad is URL pe jao
            timeout=5,                # 5 second silence ke baad submit karo
            speech_timeout="auto",    # Automatically detect karo
            language="hi"             # Fixed: Twilio expects 'hi' not 'hi-IN'
        )
        
        gather.say(first_message, voice="Polly.Aditi", language="hi-IN")
        
        response.append(gather)
        
        # Agar kuch nahi bola toh
        response.say("Main aapki awaaz nahi sun paaya. Please call back karein.", 
                     voice="Polly.Aditi", language="hi-IN")
        
        return Response(str(response), mimetype="text/xml")
    
    except Exception as e:
        logger.error(f"Error in incoming_call: {e}", exc_info=True)
        response = VoiceResponse()
        response.say("Technical issue aayi. Please baad mein call karein.", 
                     voice="Polly.Aditi", language="hi-IN")
        response.hangup()
        return Response(str(response), mimetype="text/xml")

# ─────────────────────────────────────────────
# ROUTE 2: Caller ne kuch bola — process karo
# ─────────────────────────────────────────────
@app.route("/handle-speech", methods=["POST"])
def handle_speech():
    """Caller ke speech ko AI se process karo"""
    
    try:
        caller = request.form.get("From", "Unknown")
        call_sid = request.form.get("CallSid", "")
        speech_result = request.form.get("SpeechResult", "").strip()
        
        logger.info(f"🗣️ Caller bola: {speech_result}")
        
        response = VoiceResponse()
        
        # Agar kuch nahi bola
        if not speech_result:
            gather = Gather(
                input="speech",
                action="/handle-speech",
                timeout=5,
                speech_timeout="auto",
                language="hi"
            )
            gather.say("Kya aap wahan hain? Please baat karein.", 
                       voice="Polly.Aditi", language="hi-IN")
            response.append(gather)
            return Response(str(response), mimetype="text/xml")
        
        # AI se jawab lo
        try:
            ai_reply = get_ai_response(call_sid, speech_result)
        except Exception as e:
            logger.error(f"AI response error: {e}")
            ai_reply = "Maafi chahta hoon, technical issue aayi. Baad mein try karenge."
        
        logger.info(f"🤖 AI bola: {ai_reply}")
        
        # Conversation khatam karne ke signals
        end_signals = ["dhanyawad", "thank you", "bye", "alvida", "ok bye", "theek hai", "shukriya"]
        should_end = any(signal in speech_result.lower() for signal in end_signals)
        
        if should_end:
            response.say(ai_reply + " Dhanyawad! Main aapka message note kar lunga. Namaste!", 
                         voice="Polly.Aditi", language="hi-IN")
            response.hangup()
            
            # Background mein notes save karo
            threading.Thread(
                target=save_call_notes, 
                args=(call_sid, caller),
                daemon=True
            ).start()
            
        else:
            # Continue conversation
            gather = Gather(
                input="speech",
                action="/handle-speech",
                timeout=5,
                speech_timeout="auto",
                language="hi"
            )
            gather.say(ai_reply, voice="Polly.Aditi", language="hi-IN")
            response.append(gather)
            
            # After gather, if no input, hang up instead of redirect
            response.say("Dhanyawad! Namaste!", 
                         voice="Polly.Aditi", language="hi-IN")
            response.hangup()
        
        return Response(str(response), mimetype="text/xml")
    
    except Exception as e:
        logger.error(f"Error in handle_speech: {e}", exc_info=True)
        response = VoiceResponse()
        response.say("Technical issue aayi. Call khatam ho raha hai.", 
                     voice="Polly.Aditi", language="hi-IN")
        response.hangup()
        return Response(str(response), mimetype="text/xml")


# ─────────────────────────────────────────────
# ROUTE 3: Recording callback
# ─────────────────────────────────────────────
@app.route("/record-callback", methods=["POST"])
def record_callback():
    """Recording save hone ke baad callback"""
    logger.info("Recording callback received")
    return Response("", status=204)


# ─────────────────────────────────────────────
# ROUTE 4: Call khatam — notes save karo
# ─────────────────────────────────────────────
@app.route("/end-call", methods=["POST"])
def end_call():
    """Call khatam hone pe notes save karo"""
    
    try:
        call_sid = request.form.get("CallSid", "")
        caller = request.form.get("From", "Unknown")
        
        logger.info(f"Call ending - saving notes for {caller}")
        
        response = VoiceResponse()
        response.say("Bahut shukriya aapka. Main aapka message note kar lunga. Namaste!", 
                     voice="Polly.Aditi", language="hi-IN")
        response.hangup()
        
        # Background mein notes save karo
        threading.Thread(
            target=save_call_notes, 
            args=(call_sid, caller),
            daemon=True
        ).start()
        
        return Response(str(response), mimetype="text/xml")
    
    except Exception as e:
        logger.error(f"Error in end_call: {e}", exc_info=True)
        response = VoiceResponse()
        response.hangup()
        return Response(str(response), mimetype="text/xml")


# ─────────────────────────────────────────────
# Helper: Notes save karne ka function
# ─────────────────────────────────────────────
def save_call_notes(call_sid: str, caller: str):
    """Background mein transcript + summary save karo"""
    
    try:
        logger.info(f"💾 Notes save karna shuru... (SID: {call_sid})")
        
        # Conversation history se transcript nikalo
        transcript = get_full_conversation(call_sid)
        
        if not transcript or len(transcript.strip()) < 5:
            logger.warning(f"No transcript found for call {call_sid}")
            clear_conversation(call_sid)
            return
        
        # AI se summary banwao
        logger.info("📝 Summary bana raha hai...")
        try:
            summary = summarize_call(transcript, caller)
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            summary = f"Call se transcript: {transcript[:200]}..."
        
        # Notes file mein save karo
        try:
            saved_path = save_note(caller, summary, transcript)
            logger.info(f"✅ Notes saved at: {saved_path}")
        except Exception as e:
            logger.error(f"Failed to save notes: {e}", exc_info=True)
        
        # Memory clear karo
        clear_conversation(call_sid)
    
    except Exception as e:
        logger.error(f"Error in save_call_notes: {e}", exc_info=True)


# ─────────────────────────────────────────────
# Server Start
# ─────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("🚀 AI Call Agent Server start ho raha hai...")
    logger.info("📂 Notes saved in: notes/call_notes.md")
    app.run(debug=True, port=5000)