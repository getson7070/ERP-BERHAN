FROM python:3.11-slim

RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
  CMD curl -fsS http://localhost:8000/healthz || exit 1

CMD ["gunicorn","-k","eventlet","-w","1","-b","0.0.0.0:8000","erp:create_app()","--access-logfile","-"]

