# erp/routes/analytics.py  (imports only)
from erp.observability import KPI_SALES_MV_AGE
from erp.extensions import socketio
# in erp/routes/analytics.py
try:
    from celery import Celery
    from celery.schedules import crontab
    HAVE_CELERY = True
except Exception:
    HAVE_CELERY = False
