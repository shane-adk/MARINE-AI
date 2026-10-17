# Marine Pollution AI backend - multi-arch (amd64/arm64/s390x)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    USE_MOCK=true \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
# Optional: bake the built frontend into the image
COPY frontend/dist ./frontend/dist 2>/dev/null || true

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
