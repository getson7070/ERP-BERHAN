FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN python -m pip install --upgrade pip &&     if [ -f requirements.txt ]; then pip install -r requirements.txt; fi &&     pip install . || true
EXPOSE 8000
CMD ["python","-m","http.server","8000"]
