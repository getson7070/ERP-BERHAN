# syntax=docker/dockerfile:1

# Builder stage installs dependencies to an isolated prefix
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt \
    && pip install --prefix=/install --no-cache-dir gunicorn

# Final runtime image
FROM python:3.11-slim
RUN apt-get update && apt-get install --no-install-recommends -y curl \ 
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
RUN addgroup --system app && adduser --system --ingroup app app
USER app
EXPOSE 8000
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:app"]
