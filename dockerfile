FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Build essentials for psycopg/cryptography and curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

# Install deps first to leverage Docker layer cache
COPY requirements.lock /app/requirements.lock
COPY requirements.txt  /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel && \
    if [ -f requirements.lock ]; then \
        pip install --no-cache-dir -r requirements.lock; \
    elif [ -f requirements.txt ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        echo "No requirements file found" && exit 1; \
    fi
# inside your Dockerfile
COPY dockerfile/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Bring in the app
COPY . /app

EXPOSE 18000
