FROM python:3.11-slim
WORKDIR /app
COPY REQUIREMENTS.txt .
RUN pip install --no-cache-dir -r REQUIREMENTS.txt && pip install --no-cache-dir gunicorn
COPY . .
ENV FLASK_SECRET_KEY=change-me
ENV DATABASE_PATH=/app/erp.db
ENV SESSION_LIFETIME_MINUTES=30
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:app"]
