import os
try:
    from celery import Celery
    celery = Celery('erp', broker=os.getenv('REDIS_URL', 'memory://'))
except Exception:
    celery = None

def send_approval_reminders():
    return 0

def forecast_sales():
    return []
