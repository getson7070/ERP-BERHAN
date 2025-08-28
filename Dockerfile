# syntax=docker/dockerfile:1

# Builder stage installs dependencies to an isolated prefix
FROM python:3.11-slim@sha256:8df0e8faf75b3c17ac33dc90d76787bbbcae142679e11da8c6f16afae5605ea7 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt \
    && pip install --prefix=/install --no-cache-dir gunicorn

# Final runtime image
FROM python:3.11-slim@sha256:8df0e8faf75b3c17ac33dc90d76787bbbcae142679e11da8c6f16afae5605ea7
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl wget \
    && rm -rf /var/lib/apt/lists/* \
    && adduser --disabled-password --gecos '' appuser \
    && chown -R appuser /app
COPY --from=builder /install /usr/local
COPY . .
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:app"]
