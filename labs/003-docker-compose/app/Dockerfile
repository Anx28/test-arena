# Стартовая точка лабы 002: намеренно «толстый» и наивный Dockerfile.
# Это симуляция состояния «как было до оптимизации»: полный базовый образ,
# никакой экономии слоёв, запуск от root, без HEALTHCHECK.
# Твоя задача — по шагам из README довести его до продакшен-вида.
FROM python:3.12-alpine AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1


WORKDIR /build

COPY ./app/requirements.txt .

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install -r requirements.txt



FROM python:3.12-alpine
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /srv/app

COPY --from=builder /opt/venv /opt/venv
# Копируем код приложения
COPY app/app.py .
# Создаем пользователя без root-прав (в Alpine это adduser -D)
RUN adduser -D -u 10001 appuser \
    && chown -R appuser /srv/app
USER appuser
EXPOSE 8000

# Проверка здоровья силами Python (curl в alpine нет, и ставить его не нужно!)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1
CMD ["python", "app.py"]





