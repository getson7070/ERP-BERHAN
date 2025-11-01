# Multi-stage build for ERP-BERHAN
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential libpq-dev curl &&     rm -rf /var/lib/apt/lists/*

# Copy requirement files if present, else fallback to pyproject
COPY requirements.txt* /app/ 2>/dev/null || true
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# Copy app
COPY . /app

# Default envs (override in compose/Render)
ENV FLASK_APP=erp:create_app     FLASK_ENV=production     GUNICORN_CMD_ARGS="--workers=3 --threads=4 --timeout=120"

# Create a non-root user
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

# Entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# Default launch
CMD ["web"]
