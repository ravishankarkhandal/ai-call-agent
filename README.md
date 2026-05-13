# AI Call Agent - Setup Guide

## 🚀 Quick Setup

### 1. Clone/Setup Environment
```bash
cd ai-call-agent
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
# Copy the example file
copy .env.example .env

# Edit .env and add your credentials:
# - Twilio Account SID
# - Twilio Auth Token
# - Twilio Phone Number
# - OpenAI API Key
```

### 4. Run the Application
```bash
python app.py
```

The server will start on `http://localhost:5000`

---

## 🔧 Configuration

### Environment Variables Required:
- `TWILIO_ACCOUNT_SID` - Your Twilio account SID
- `TWILIO_AUTH_TOKEN` - Your Twilio auth token
- `TWILIO_PHONE_NUMBER` - Your Twilio phone number (format: +1234567890)
- `OPENAI_API_KEY` - Your OpenAI API key

### Optional:
- `FLASK_ENV` - Set to 'production' for production deployment
- `FLASK_DEBUG` - Set to 0 for production

---

## 📞 How It Works

1. **Incoming Call** → `/incoming-call`
   - AI agent greets the caller
   - Starts listening to caller's message

2. **Processing Speech** → `/handle-speech`
   - AI processes caller's message
   - Generates appropriate response
   - Continues conversation or ends call

3. **Call Ends** → Notes saved
   - Conversation transcript saved
   - AI-generated summary created
   - Both stored in `notes/call_notes.md`

---

## 📂 Project Structure

```
ai-call-agent/
├── app.py              # Main Flask application
├── ai_handler.py       # AI response handling
├── summarizer.py       # Transcript summarization
├── transcriber.py      # Call recording transcription
├── notes_manager.py    # Notes file management
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── .gitignore          # Git ignore file
└── notes/              # Saved call notes (auto-created)
    └── call_notes.md   # Call transcripts and summaries
```

---

## 🔍 Troubleshooting

### Issue: "OPENAI_API_KEY not found"
- Solution: Check `.env` file and ensure OPENAI_API_KEY is set

### Issue: "Twilio credentials not found"
- Solution: Check `.env` for TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER

### Issue: No notes being saved
- Solution: Check that `notes/` directory has write permissions

### Issue: Call transcription fails
- Solution: Ensure OpenAI quota is available and recording URL is accessible

### Issue: AI responses are too slow
- Solution: Normal for first response. Subsequent responses should be faster.

---

## 🔒 Security Notes

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Use `.env.example`** - As a template for configuration
3. **Rotate API keys regularly** - Keep credentials secure
4. **Use environment variables** - Don't hardcode credentials

---

## 📊 Logs and Debugging

Logs are printed to console. For production, configure proper logging:

```python
# In app.py, configure file logging
import logging.handlers
handler = logging.handlers.RotatingFileHandler('app.log', maxBytes=10485760, backupCount=5)
```

---

## 🧹 Maintenance

### Regular Tasks:
1. **Archive old notes** - Move call_notes.md to backup when it gets large
2. **Monitor API usage** - Check OpenAI and Twilio dashboards
3. **Update dependencies** - Run `pip install --upgrade -r requirements.txt`
4. **Review logs** - Check for errors and unusual patterns

### Cleanup:
```bash
# Remove old notes backup
rm notes/call_notes.md.backup

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
```

---

## 🚀 Production Deployment

### Using Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

---

## 📞 Support & Troubleshooting

For issues:
1. Check `ISSUES_FIXED.md` for known issues
2. Review error logs
3. Verify all environment variables are set
4. Test API keys independently
5. Check Twilio and OpenAI console for errors

---

## 📝 License & Credits

- **Twilio** - Voice API
- **OpenAI** - GPT-4o-mini for AI responses and Whisper for transcription
- **Flask** - Web framework
