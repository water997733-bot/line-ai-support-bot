import os
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"


@app.get("/")
def home():
    return {"status": "LINE AI Support Bot is running"}


@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    events = body.get("events", [])

    for event in events:
        if event.get("type") == "message":
            reply_token = event.get("replyToken")
            message = event.get("message", {})
            user_text = message.get("text", "")

            reply_text = f"我已收到你的問題：{user_text}\n\n目前 AI 技術支援系統建置中。"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            }

            payload = {
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": reply_text}],
            }

            requests.post(LINE_REPLY_URL, headers=headers, json=payload)

    return {"status": "ok"}
