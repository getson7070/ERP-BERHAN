# syntax=docker/dockerfile:1

# Builder stage installs dependencies to an isolated prefix
FROM python:3.11-slim@sha256:8df0e8faf75b3c17ac33dc90d76787bbbcae142679e11da8c6f16afae5605ea7 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt \
    && pip install --prefix=/install --no-cache-dir gunicorn

# Final runtime image
FROM python:3.11-slim@sha256:8df0e8faf75b3c17ac33dc90d76787bbbcae142679e11da8c6f16afae5605ea7
RUN apt-get update && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
RUN addgroup --system app && adduser --system --ingroup app app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:app"]
