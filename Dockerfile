FROM node:22-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
COPY shared/ /build/shared/
RUN npm run build
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.lock /app/backend/requirements.lock
RUN pip install --no-cache-dir -r backend/requirements.lock
COPY backend/ /app/backend/
COPY shared/ /app/shared/
COPY --from=frontend /build/frontend/dist /app/frontend/dist
RUN mkdir -p /app/.local
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
