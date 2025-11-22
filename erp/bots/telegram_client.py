"""Telegram transport helpers with inline keyboard support."""
from __future__ import annotations

import requests
from flask import current_app


def _bot_token(bot_name: str) -> str:
    bots = current_app.config.get("TELEGRAM_BOTS") or {}
    token = bots.get(bot_name)
    if not token:
        raise RuntimeError(f"Unknown bot_name={bot_name}")
    return token


def telegram_send(bot_name: str, chat_id: str, payload: dict):
    token = _bot_token(bot_name)
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": payload.get("text", ""),
        "parse_mode": payload.get("parse_mode", "HTML"),
        "disable_web_page_preview": True,
    }

    kb = payload.get("keyboard") or {}
    if kb.get("inline"):
        data["reply_markup"] = {"inline_keyboard": kb["inline"]}
    elif kb.get("reply"):
        data["reply_markup"] = {
            "keyboard": kb["reply"],
            "resize_keyboard": True,
            "one_time_keyboard": kb.get("one_time", False),
        }

    response = requests.post(url, json=data, timeout=20)
    response.raise_for_status()
    return response.json()


def telegram_edit(bot_name: str, chat_id: str, message_id: str, payload: dict):
    token = _bot_token(bot_name)
    url = f"https://api.telegram.org/bot{token}/editMessageText"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": payload.get("text", ""),
        "parse_mode": payload.get("parse_mode", "HTML"),
        "disable_web_page_preview": True,
    }
    response = requests.post(url, json=data, timeout=20)
    response.raise_for_status()
    return response.json()


def telegram_answer_callback(bot_name: str, callback_query_id: str, text: str = "OK"):
    token = _bot_token(bot_name)
    url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
    data = {"callback_query_id": callback_query_id, "text": text}
    response = requests.post(url, json=data, timeout=10)
    response.raise_for_status()
    return response.json()
