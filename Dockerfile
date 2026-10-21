# Railway: build the React frontend and serve it with the same FastAPI origin.
# Multi-stage build keeps Node.js out of the running Python container.
FROM node:22-bookworm-slim AS frontend-builder
WORKDIR /workspace/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY api/ ./api/
COPY blockchain/artifact.json ./blockchain/artifact.json
COPY assets/fonts/ ./assets/fonts/
COPY --from=frontend-builder /workspace/frontend/dist/ ./frontend/dist/
EXPOSE 8080
CMD ["sh","-c","exec python -m uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
