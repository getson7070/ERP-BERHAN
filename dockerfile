# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

# Minimal OS deps (drop build-essential; keep curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Install runtime deps with cache (BuildKit)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy app source last to maximize cache hits
COPY . .

# No CMD here; docker-compose.yml provides the gunicorn command
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=10 CMD curl -fsS http://localhost:8000/health/ready || exit 1


# normalize line endings & executable bit for entrypoint
RUN sed -i 's/\r$//' docker/entrypoint.sh && chmod +x docker/entrypoint.sh

