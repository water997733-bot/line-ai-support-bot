import os
import requests
from fastapi import FastAPI, Request, Response
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI()

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

GRAPH_API_VERSION = "v19.0"

client = OpenAI(api_key=OPENAI_API_KEY)


@app.get("/")
def home():
    return {"status": "WhatsApp AI Support Bot is running"}


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")

    return Response(content="Forbidden", status_code=403)


@app.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()

    try:
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "no message"}

        message = messages[0]
        from_number = message.get("from")
        message_type = message.get("type")

        if message_type == "text":
            user_text = message.get("text", {}).get("body", "")
            print(f"收到訊息：{user_text}")
            reply_text = get_ai_reply(user_text)
            send_whatsapp_message(from_number, reply_text)

    except Exception as e:
        print("Error:", e)

    return {"status": "ok"}


def get_ai_reply(user_text: str) -> str:
    try:
        print("呼叫 OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是 ITE SoC SDK/HDK 技術支援助理。"
                        "請用繁體中文回答技術問題。"
                        "回答要簡潔清楚，如果不確定答案請說明。"
                    )
                },
                {
                    "role": "user",
                    "content": user_text
                }
            ],
            max_tokens=500
        )
        reply = response.choices[0].message.content
        print(f"OpenAI 回覆：{reply}")
        return reply
    except Exception as e:
        print("OpenAI Error:", e)
        return "抱歉，AI 系統暫時無法回應，請稍後再試。"


def send_whatsapp_message(to: str, text: str):
    url = (
        f"https://graph.facebook.com/{GRAPH_API_VERSION}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    response = requests.post(url, headers=headers, json=payload)
    print("WhatsApp API response:", response.status_code, response.text)
