# Стартовая точка лабы 002: намеренно «толстый» и наивный Dockerfile.
# Это симуляция состояния «как было до оптимизации»: полный базовый образ,
# никакой экономии слоёв, запуск от root, без HEALTHCHECK.
# Твоя задача — по шагам из README довести его до продакшен-вида.
FROM python:3.12

WORKDIR /app

COPY ./app/requirements.txt .
RUN pip install -r requirements.txt

COPY ./app/app.py .

EXPOSE 8000

CMD ["python3", "app.py"]
