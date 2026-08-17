import os
import requests
from flask import Flask, request

app = Flask(__name__)

# List of all your Telegram Bot Tokens (Add as many as you want here!)
TELEGRAM_TOKENS = [
    os.environ.get("TELEGRAM_BOT_TOKEN") or "8996950974:AAEX0fr9WLs7iN-zm4knOqQMCFG5SLWLhiA",
    # Add your second bot token here when you make it:
    # "ANOTHER_BOT_TOKEN_HERE"
]

# PASTE YOUR BRAND NEW GROQ API KEY INSIDE THE QUOTES BELOW:
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or "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"

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Dictionary to store conversation history per chat_id (Short-term memory)
chat_histories = {}

@app.route('/')
def home():
    return "🤖 Multi-Bot Telegram AI is alive and running!"

# Dynamic route that catches updates for ANY of your bot tokens
@app.route("/<token>", methods=['POST'])
def telegram_webhook(token):
    # Verify the token is one of ours for security
    if token not in TELEGRAM_TOKENS:
        return "Unauthorized", 403
        
    update = request.get_json()
    
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_message = update["message"]["text"]
        
        # Initialize history for this user if it doesn't exist yet
        if chat_id not in chat_histories:
            chat_histories[chat_id] = [
                {"role": "system", "content": "You are a friendly, helpful AI assistant built by Hudson. Use emojis and keep responses engaging!"}
            ]
        
        # Add user message to history
        chat_histories[chat_id].append({"role": "user", "content": user_message})
        
        # Keep only the last 10 messages so it stays fast and focused
        if len(chat_histories[chat_id]) > 11:
            chat_histories[chat_id] = [chat_histories[chat_id][0]] + chat_histories[chat_id][-10:]
        
        # Call Groq AI with the full history
        ai_reply = ask_groq(chat_histories[chat_id])
        
        # Add AI response to history
        chat_histories[chat_id].append({"role": "assistant", "content": ai_reply})
        
        # Send reply back using the specific bot token that received the message
        send_telegram_message(token, chat_id, ai_reply)
        
    return "OK", 200

def ask_groq(messages_history):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": messages_history
    }
    try:
        response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=15)
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        else:
            print(f"Groq API Error Response: {data}")
            return f"Groq Error: {data.get('error', {}).get('message', 'Unknown error')}"
            
    except Exception as e:
        print(f"Connection Exception: {e}")
        return f"Failed to connect to Groq API: {e}"

def send_telegram_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
