# Multi-tenant ERP-BERHAN Dockerfile
# Clean, production-ready base with no reliance on the host .venv

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for building some Python packages (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ------------------------------------------------------------------
# Install Python dependencies
# ------------------------------------------------------------------
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------------
# Copy application source
# ------------------------------------------------------------------
COPY . .

# Create non-root user for better security
RUN useradd -m appuser
USER appuser

# Expose the app port (inside the container).
EXPOSE 8000

# ------------------------------------------------------------------
# Default command:
# - Run init_db.py to ensure schema + seeds
# - Start the app via gunicorn using the Flask app factory
# ------------------------------------------------------------------
CMD ["sh", "-c", "python init_db.py && gunicorn -b 0.0.0.0:8000 'erp.app:create_app()'"]
