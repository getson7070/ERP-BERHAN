FROM python:3.11-slim

# 1) System deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

# 2) App base
WORKDIR /app

# 3) Python deps from lock file + extras we know we need
COPY requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir -r /app/requirements.lock \
    && pip install --no-cache-dir pip-tools "psycopg[binary]"

# 4) Copy project
COPY . /app

# 5) Normalize entrypoint line endings & make executable
RUN sed -i 's/\r$//' docker/entrypoint.sh && chmod +x docker/entrypoint.sh

# 6) Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 18000

# 7) Use our entrypoint; default command is "web"
ENTRYPOINT ["docker/entrypoint.sh"]
CMD ["web"]
