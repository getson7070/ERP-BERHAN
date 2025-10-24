import os, multiprocessing
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8080")
workers = int(os.getenv("WEB_CONCURRENCY", str(max(2, multiprocessing.cpu_count()//2))))
threads = int(os.getenv("GUNICORN_THREADS", "2"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
accesslog = "-"
errorlog = "-"
worker_tmp_dir = "/dev/shm"
forwarded_allow_ips = "*"
# Keepalive avoids idle disconnects behind some proxies
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
