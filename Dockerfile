FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app_with_cookies.py .
COPY script.py .
COPY passenger_wsgi.py .
COPY templates/ templates/
COPY static/ static/

EXPOSE 5000

ENV FLASK_APP=app_with_cookies.py
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "--workers", "3", "--worker-class", "gthread", "--threads", "4", "--timeout", "240", "--bind", "0.0.0.0:5000", "app_with_cookies:app"]
