# Один образ для всех python-сервисов стенда: только stdlib, без зависимостей.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 DATA_DIR=/app/data
WORKDIR /app
COPY services/*.py ./
COPY data ./data
USER 10001
