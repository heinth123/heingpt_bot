import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or "8996950974:AAEX0fr9WLs7iN-zm4knOqQMCFG5SLWLhiA"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or "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"

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route('/')
def home():
    return "🤖 Telegram AI Bot is alive and running!"

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=['POST'])
def telegram_webhook():
    update = request.get_json()
    
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_message = update["message"]["text"]
        
        ai_reply = ask_groq(user_message)
        send_telegram_message(chat_id, ai_reply)
        
    return "OK", 200

def ask_groq(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a friendly, helpful AI assistant built by Hudson. Use emojis and keep responses engaging!"},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=15)
        data = response.json()
        
        # Check if Groq returned choices
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        else:
            # Print error response to Render logs for debugging
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
