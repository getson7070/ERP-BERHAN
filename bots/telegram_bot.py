from flask import request

def telegram_webhook():
    data = request.json
    return "Handled"
