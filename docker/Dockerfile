FROM python:3.12-slim
WORKDIR /app
COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/main.py .

EXPOSE 9223

CMD ["gunicorn", "--bind", "0.0.0.0:9223", "--workers", "2", "--timeout", "30", "main:app"]
