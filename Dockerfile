# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps only if you really need them; keep slim.
# RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Install dependencies first (layer cache)
COPY requirements.lock requirements.txt /app/
RUN python -m pip install --upgrade pip setuptools wheel && \
    if [ -f requirements.lock ]; then pip install -r requirements.lock; else pip install -r requirements.txt; fi

# Copy the application
COPY . /app

# Expose is informational; App Runner sets the port via $PORT
EXPOSE 8000

# Let App Runner provide $PORT; default to 8000 locally
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8000} wsgi:app"]
