FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.lock requirements.txt /app/
RUN python -m pip install --upgrade pip setuptools wheel && \
    if [ -f requirements.lock ]; then pip install -r requirements.lock; else pip install -r requirements.txt; fi

COPY . /app

RUN addgroup --system app && adduser --system --ingroup app app
USER app

EXPOSE 8000
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8000} wsgi:app"]
