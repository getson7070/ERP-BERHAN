# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl gcc git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt* requirements-dev.txt* ./

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip && \
    ( test -f requirements.txt && pip install -r requirements.txt || true ) && \
    ( test -f requirements-dev.txt && pip install -r requirements-dev.txt || true ) && \
    pip install gunicorn eventlet gevent gevent-websocket pip-audit

COPY . .

ENV GUNICORN_CMD_ARGS="--workers=1 --worker-class=eventlet --timeout=120 --access-logfile - --error-logfile -"
ENV HEALTHCHECK_PATH=/status
EXPOSE 8000
ENV FLASK_ENV=production

CMD ["gunicorn", "-b", "0.0.0.0:8000", "deploy.wsgi:app"]