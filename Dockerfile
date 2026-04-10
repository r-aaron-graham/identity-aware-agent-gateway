FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

ENV IAAG_DB_PATH=/app/data/iaag.db
ENV IAAG_SECRET_KEY=change-me
ENV IAAG_AUTO_INIT_DB=true

CMD ["bash", "-lc", "python scripts/seed.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
