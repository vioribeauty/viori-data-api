FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run migrations then start server
CMD ["sh", "-c", "python migrate_sqlite.py --if-empty && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
