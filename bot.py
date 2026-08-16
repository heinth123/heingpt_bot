import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Your secure Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or "8996950974:AAEX0fr9WLs7iN-zm4knOqQMCFG5SLWLhiA"

# PASTE YOUR FRESH GROQ API KEY INSIDE THE QUOTES BELOW:
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or "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"

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Dictionary to store conversation history per chat_id
# Format: { chat_id: [ {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ... ] }
chat_histories = {}

@app.route('/')
def home():
    return "🤖 Telegram AI Bot with Memory is alive and running!"

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=['POST'])
def telegram_webhook():
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
        
        # Keep only the last 10 messages so it doesn't get overloaded (memory window)
        if len(chat_histories[chat_id]) > 11: # 1 system prompt + 10 chat messages
            # Keep system prompt at index 0, and slice the latest 10 messages
            chat_histories[chat_id] = [chat_histories[chat_id][0]] + chat_histories[chat_id][-10:]
        
        # Call Groq AI with the full history
        ai_reply = ask_groq(chat_histories[chat_id])
        
        # Add AI response to history
        chat_histories[chat_id].append({"role": "assistant", "content": ai_reply})
        
        # Send reply back to Telegram
        send_telegram_message(chat_id, ai_reply)
        
    return "OK", 200

def ask_groq(messages_history):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
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

def send_telegram_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
