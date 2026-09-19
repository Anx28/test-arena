# Лабораторная 001 — Первый Dockerfile

## Цель

Написать `Dockerfile` для простого Flask-приложения, собрать образ на своём сервере,
запустить контейнер и убедиться, что приложение отвечает. После этой лабораторной
ты сможешь объяснять, что такое образ, контейнер, слои и контекст сборки.

## Требования к окружению

Сервер, на котором ты будешь работать:

- Linux (рекомендуется Ubuntu 22.04+ или Debian 12+)
- доступ по SSH
- **Docker Engine 24+** — проверка: `docker --version`
- **git** — проверка: `git --version`
- **curl** — проверка: `curl --version`

Быстрая самопроверка (должна вывести успешное сообщение):

```bash
docker run --rm hello-world
```

## Что уже есть в каталоге лабораторной

| Файл | Назначение |
|------|------------|
| `app/app.py` | Flask-приложение: два эндпоинта `/` и `/health`, слушает порт **8000** |
| `app/requirements.txt` | Зависимости приложения (flask, зафиксированная версия) |
| `.dockerignore` | Что НЕ должно попадать в контекст сборки (пример, можешь доработать) |

Код приложения можно посмотреть, но **менять его не нужно** (можно — но только
осознанно, например, для бонусных задач).

Опционально, до Docker — запусти приложение «голым», чтобы понимать, что упаковываешь:

```bash
cd app
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
# в другом терминале:
curl http://localhost:8000/
curl http://localhost:8000/health
# останови: Ctrl+C
```

## Задание

### Шаг 1. Склонируй репозиторий и заходи в лабораторную

```bash
git clone https://github.com/Anx28/test-arena.git
cd test-arena/labs/001-first-dockerfile
```

### Шаг 2. Напиши Dockerfile

Создай файл `Dockerfile` **в этом же каталоге** (рядом с `app/`). Требования к нему:

- базовый образ — Python (подбери сам: `python:3.12`, `python:3.12-slim`, ... —
  подумай, чем отличаются, и запиши свой выбор в заметки);
- в образ попадают код приложения и его зависимости (установленные из
  `requirements.txt`);
- объявлен порт 8000;
- при старте контейнера приложение запускается само — `docker run` без командного аргумента.

Можно начать с такого скелета:

```dockerfile
FROM python:3.12-slim

# ... твои команды:
# WORKDIR, COPY, RUN, ENV, EXPOSE, CMD
```

Полезные инструкции и их смысл: `FROM`, `WORKDIR`, `COPY`, `RUN`, `ENV`, `EXPOSE`,
`USER`, `HEALTHCHECK`, `CMD`, `ENTRYPOINT`. Документация:
https://docs.docker.com/reference/dockerfile/

### Шаг 3. Собирай образ

```bash
docker build -t lab01:0.1 .
```

- имя образа — `lab01`, тег — `0.1`;
- точка в конце — **контекст сборки**: это каталог, из которого Docker берёт файлы
  (в нём же лежит и сам `Dockerfile`).
- Посмотри, какие слои добавил Docker: `docker history lab01:0.1`.

### Шаг 4. Запускай контейнер

```bash
docker run --rm -d -p 8000:8000 --name lab01 lab01:0.1
```

Расшифровка (проверь, что понимаешь каждый флаг): `--rm`, `-d`, `-p 8000:8000`, `--name`.

### Шаг 5. Проверяй результат

```bash
curl http://localhost:8000/
curl http://localhost:8000/health
```

Ожидаемый ответ: JSON-объект с сообщением «Привет, DevOps!» и `{"status": "ok"}`.

Осмотри артефакты и объясни себе, что видишь:

```bash
docker images            # есть ли lab01:0.1, какой размер
docker ps                # контейнер lab01: статус Up, маппинг портов
docker logs lab01        # логи запуска Flask
docker inspect lab01 | head -50   # детали: порты, образ, user и т.д.
docker history lab01:0.1 # слои твоего образа
```

### Шаг 6. Убери за собой

```bash
docker rm -f lab01       # остановить и удалить контейнер
docker rmi lab01:0.1     # удалить образ (по желанию — оставишь, пригодится для бонусов)
```

## Бонусы (необязательно, но очень учат)

1. **Кэш слоёв.** Смотри `docker history lab01:0.1`. Переставь команды так, чтобы
   изменение `app/app.py` НЕ приводило к переустановке зависимостей.
   Пересобери образ дважды (вторая — без изменений) и сравни время сборки.
   Запиши, почему порядок команд влияет на кэш.
2. **Non-root.** Добавь в Dockerfile `USER` — приложение должно работать
   не под root. Проверь: `docker exec lab01 id`.
3. **Healthcheck.** Добавь `HEALTHCHECK` (подсказка: `curl` или `python -c ...`
   к `/health`). Проверь:
   `docker inspect --format='{{.State.Health.Status}}' lab01` — через минуту должно стать `healthy`.
4. **Почти прод.** Замени встроенный сервер Flask на gunicorn:
   добавь его в `requirements.txt`, запуск —
   `CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]`. Подумай: что это даёт?

## Критерий готовности

- [ ] `Dockerfile` написан в каталоге лабораторной
- [ ] `docker build -t lab01:0.1 .` — образ собран
- [ ] `docker run --rm -d -p 8000:8000 lab01:0.1` — контейнер работает
- [ ] `curl http://localhost:8000/` и `/health` возвращают JSON
- [ ] Ты можешь объяснить: что такое слои, контекст сборки, и зачем
      `COPY requirements.txt` идёт до `COPY app/`
- [ ] Отвечены контрольные вопросы ниже

## Контрольные вопросы

1. Почему `COPY requirements.txt` + `RUN pip install` идут **до** копирования всего
   кода? Что происходит при повторной сборке, если поменялась только `app.py`?
2. Чем `EXPOSE 8000` отличается от `-p 8000:8000` в `docker run`?
   Сработает ли проброс портов, если убрать `EXPOSE` из Dockerfile?
3. Что такое контекст сборки? Почему без `.dockerignore` в образ может «случайно»
   попасть `.git` (и что это значит по размеру)?
4. `CMD` или `ENTRYPOINT` — какой ты использовал и почему для этого приложения
   он подходит?
5. Какой у твоего образ размер (`docker images`)? Что, по-твоему, занимает больше
   всего: Python, Flask или код приложения?
6. Почему в `app.py` задан `host="0.0.0.0"`, а не просто `app.run(port=8000)`?

## Референсное решение

<details>
<summary>Открывай только после того, как сам написал и собрал Dockerfile</summary>

```dockerfile
# Dockerfile для лабы 001: Flask-приложение в контейнере
FROM python:3.12-slim

# Python в Docker: не писать байткод и не буферизовать логи
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv/app

# Сначала зависимости: пока requirements.txt не меняется,
# этот слой (с установленным Flask) берётся из кэша
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Теперь сам код приложения
COPY app/app.py .

# Документация о порте (сам по себе проброс не выполняет — это делает -p)
EXPOSE 8000

# Проверка живости контейнера
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

# Запускать приложение не под root
USER nobody

CMD ["python", "app.py"]
```

Быстрая проверка:

```bash
docker build -t lab01:0.1 .
docker run --rm -d -p 8000:8000 --name lab01 lab01:0.1
curl http://localhost:8000/
curl http://localhost:8000/health
docker inspect --format='{{.State.Health.Status}}' lab01   # через ~40 сек: healthy
```

</details>

## Если что-то пошло не так

| Симптом | Что проверить |
|---------|---------------|
| `docker build` падает на `pip install` | Сетевой доступ сервера в интернет; содержимое `requirements.txt`; права на чтение файла |
| `curl: (7) Failed to connect` | Контейнер жив (`docker ps`)? `-p 8000:8000` указан? `docker logs lab01` — запустился ли Flask, не на том ли порту |
| Flask в логах слушает `127.0.0.1:8000` | `host="0.0.0.0"` в `app.py` (не должен был меняться, но проверь) |
| Порт 8000 уже занят на сервере | `sudo ss -tlnp \| grep 8000` — кто-то уже слушает; запусти на другом: `-p 8080:8000` и `curl http://localhost:8080/` |
| `permission denied` при `docker build` | Пользователь не в группе `docker` (см. секцию 0 в `docs/plan.md`), либо нужен `sudo` |
