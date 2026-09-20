"""Лаба 002: то же Flask-приложение, что и в лабе 001 — меняем обвязку, не код.

Эндпоинты:
    GET /        — приветствие (лаборная + сообщение)
    GET /health  — проверка живости (будет использоваться для docker HEALTHCHECK)

Порт: 8000.
"""
from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def index():
    return jsonify(
        lab="002-dockerfile-best-practices",
        message="Привет, DevOps! Лабораторная 002: этот ответ отдаёт образ, "
                "собранный по лучшим практикам.",
    )


@app.get("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    # host=0.0.0.0 обязателен: иначе Flask слушает только 127.0.0.1 ВНУТРИ
    # контейнера, и наружу (через -p 8000:8000) приложение не достучаться.
    app.run(host="0.0.0.0", port=8000)
