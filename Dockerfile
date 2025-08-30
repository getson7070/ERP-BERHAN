# syntax=docker/dockerfile:1

# Builder stage installs dependencies to an isolated prefix
FROM python:3.11-slim@sha256:8df0e8faf75b3c17ac33dc90d76787bbbcae142679e11da8c6f16afae5605ea7 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt \
    && pip install --prefix=/install --no-cache-dir gunicorn

# Final runtime image
FROM python:3.11-slim@sha256:8df0e8faf75b3c17ac33dc90d76787bbbcae142679e11da8c6f16afae5605ea7
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl chromium nodejs npm \
    libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0 libnss3 \
    libasound2t64 libx11-xcb1 libxss1 libgdk-pixbuf2.0-0 libxshmfence1 libdrm2 \
    && npm install -g pa11y \
    && curl -sSfL https://github.com/gitleaks/gitleaks/releases/download/v8.28.0/gitleaks_8.28.0_linux_x64.tar.gz \
         | tar xz -C /usr/local/bin gitleaks \
    && curl -sSfL https://raw.githubusercontent.com/zaproxy/zaproxy/main/docker/zap-baseline.py \
         -o /usr/local/bin/zap-baseline.py \
    && curl -sSfL https://raw.githubusercontent.com/zaproxy/zaproxy/main/docker/zap_common.py \
         -o /usr/local/bin/zap_common.py \
    && chmod +x /usr/local/bin/zap-baseline.py \
    && pip install --no-cache-dir python-owasp-zap-v2.4 \
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
