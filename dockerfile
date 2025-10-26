# Drop-in Dockerfile replacement (optional) – uses erp.app:create_app()
FROM python:3.11-slim AS base
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV APP_HOST=0.0.0.0 APP_PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=10 CMD curl -fsS http://localhost:8000/healthz || exit 1

USER root
CMD ["gunicorn","-w","4","-k","gthread","-b","0.0.0.0:8000","erp.app:create_app()"]

ENV PIP_DEFAULT_TIMEOUT=180
# (Optional) You can also set a fast mirror here if you have one
# ENV PIP_INDEX_URL=https://pypi.org/simple

RUN pip install --no-cache-dir --retries 5 --timeout 180 -r requirements.txt
