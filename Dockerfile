FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY gamemode.py .

EXPOSE 5050

# Production WSGI server (not Flask's built-in app.run)
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "2", "--threads", "4", "gamemode:app"]
