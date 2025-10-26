# erp/blueprints/telegram_webhook.py
import os, requests
from flask import Blueprint, request, jsonify
bp = Blueprint("telegram_webhook", __name__, url_prefix="/bot/telegram")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_IDS = {int(x) for x in os.getenv("TELEGRAM_ALLOWED_USER_IDS","").split(",") if x.strip().isdigit()}

def send_message(chat_id: int, text: str):
    if not BOT_TOKEN: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

@bp.post("/webhook")
def webhook():
    if not BOT_TOKEN:
        return jsonify({"ok": False, "error": "bot not configured"}), 400
    update = request.get_json(force=True, silent=True) or {}
    msg = (update.get("message") or {}) 
    chat = msg.get("chat") or {}
    user = msg.get("from") or {}
    chat_id = chat.get("id")
    user_id = user.get("id")
    if user_id not in ALLOWED_IDS:
        send_message(chat_id, "Access denied.")
        return jsonify({"ok": True})
    text = (msg.get("text") or "").strip().lower()
    if text in ("/start","help"):
        send_message(chat_id, "Hello. Your access is confirmed.")
    elif text == "health":
        send_message(chat_id, "OK")
    else:
        send_message(chat_id, f"Echo: {text}")
    return jsonify({"ok": True})
