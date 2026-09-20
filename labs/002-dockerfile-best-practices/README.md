# Лабораторная 002 — Лучшие практики Dockerfile

## Цель

«Доточить» образ из лабы 001 до приличного состояния: заметно **уменьшить размер**,
запустить приложение от **non-root** пользователя, добавить **HEALTHCHECK** и освоить
**многоэтапную сборку (multi-stage)**. После этой лабораторной у тебя будет короткий
чек-лист «как писать Dockerfile, за который не стыдно в проде», и ты сможешь его
применить к любому проекту.

**Предполагается**, что лаба 001 выполнена: ты умеешь собирать образ, запускать
контейнер и знаешь, что такое слои и контекст сборки. Если что-то забыл — перечитай
`labs/001-first-dockerfile/README.md`.

## Требования к окружению

Те же, что и для лабы 001:

- Linux (рекомендуется Ubuntu 22.04+ или Debian 12+), доступ по SSH
- **Docker Engine 24+** — проверка: `docker --version`
- **git**, **curl**
- `docker run --rm hello-world` отработал успешно

## Что уже есть в каталоге лабораторной

| Файл | Назначение |
|------|------------|
| `app/app.py` | То же Flask-приложение, что в лабе 001: эндпоинты `/` и `/health`, порт **8000** |
| `app/requirements.txt` | Зависимости приложения (flask, зафиксированная версия) |
| `Dockerfile` | **Стартовая точка**: намеренно наивный и «толстый» вариант — его ты и будешь улучшать |
| `.dockerignore` | Что НЕ должно попадать в контекст сборки |

Код приложения менять не нужно — вся работа в этой лабе происходит в `Dockerfile`.

> Если у тебя остался твой собственный `Dockerfile` из лабы 001 — можешь работать
> с ним вместо стартового. Стартовый файл здесь специально написан «в лоб» на полном
> базовом образе, чтобы прогресс по размеру был наглядным.

## Задание

Заведи заметки (файл `notes.md` прямо в каталоге лабы или свой блокнот): по ходу
лабы туда придётся записывать размеры образов и выводы. В образ `notes.md` не попадёт —
`.dockerignore` исключает `*.md`.

### Шаг 1. Замерь стартовый («толстый») образ

```bash
docker build -t lab02:before .
docker images lab02:before
docker history lab02:before
```

- Запиши размер в заметки — это точка отсчёта.
- Посмотри в `docker history`, сколько весит каждый слой. Какой слой самый тяжёлый?
  (Подсказка: это не твой код.)

Если ты делал лабу 001 на `python:3.12-slim` и образ ещё жив — замерь и его:
`docker images | grep lab01`. Дальше в лабе сравниваешь всё со стартовым `lab02:before`.

Ориентиры по размерам базовых образов (запиши свои реальные значения —
они зависят от версии и платформы):

| Базовый образ | Примерный размер | Что внутри |
|---------------|------------------|------------|
| `python:3.12` | ~1 ГБ | полный дистрибутив + компиляторы + документация |
| `python:3.12-slim` | ~130 МБ | минимальный Debian только с рантаймом |
| `python:3.12-alpine` | ~50 МБ | Alpine Linux + Python (musl вместо glibc) |

### Шаг 2. Уменьши образ: базовый образ + дисциплина установки пакетов

Внеси в `Dockerfile` изменения:

1. Смени базовый образ на `python:3.12-slim` или `python:3.12-alpine`
   (подумай, чем они отличаются, — это контрольный вопрос №1).
2. Добавь правильные переменные окружения для Python в контейнере:

   ```dockerfile
   ENV PYTHONDONTWRITEBYTECODE=1 \
       PYTHONUNBUFFERED=1 \
       PIP_NO_CACHE_DIR=1 \
       PIP_DISABLE_PIP_VERSION_CHECK=1
   ```

3. Ставь зависимости с `--no-cache-dir` (на случай, если уберёшь `PIP_NO_CACHE_DIR`):
   `pip install --no-cache-dir -r requirements.txt`.
4. Проверь, что порядок команд кэш-дружелюбный: `requirements.txt` копируется и
   устанавливается **до** копирования кода (это ты уже делал в лабе 001).

Пересобери и сравни:

```bash
docker build -t lab02:slim .
docker images | grep lab02
```

Запиши размер в заметки: насколько похудел образ и за счёт чего?

### Шаг 3. Запусти приложение от non-root

Зачем: если в приложении найдётся уязвимость (например, RCE), атакующий получит
права того пользователя, под которым работает процесс. Пусть лучше это будет
пользователь без прав.

Добавь в `Dockerfile` создание пользователя и переключение на него:

- для `slim` (Debian): `RUN useradd --create-home --uid 10001 appuser && chown -R appuser /srv/app`
- для `alpine`: `RUN adduser -D -u 10001 appuser`

и ниже: `USER appuser` (до `CMD`).

Проверь:

```bash
docker build -t lab02:nonroot .
docker run --rm -d -p 8000:8000 --name lab02 lab02:nonroot
curl http://localhost:8000/health
docker exec lab02 id          # uid=10001(appuser), НЕ 0
docker exec lab02 whoami      # appuser
```

Подумай: какие пути в образе должен мочь писать `appuser`, а какие — не должен?

### Шаг 4. Добавь HEALTHCHECK

Docker умеет сам следить, живо ли приложение внутри контейнера. Добавь:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1
```

Почему `python -c`, а не `curl`: в `slim`/`alpine` курла из коробки нет, а тянуть
его в образ ради одной проверки — лишние мегабайты и дырки в безопасности.
Интерпретатор в образе точно есть.

Проверь:

```bash
docker build -t lab02:health .
docker run --rm -d -p 8000:8000 --name lab02 lab02:health
docker inspect --format='{{.State.Health.Status}}' lab02   # сразу: starting
sleep 40
docker inspect --format='{{.State.Health.Status}}' lab02   # должно стать: healthy
```

Сломай эндпоинт мысленно (или реально: запусти любой другой порт) и посмотри,
как контейнер переходит в `unhealthy` после `retries` неудачных проверок.

### Шаг 5. Многоэтапная сборка (multi-stage)

Идея: в первом этапе («сборочном») можно держать компиляторы, кэши и весь мусор —
а в финальный образ копировать только готовый результат.

Перепиши `Dockerfile` в два этапа:

1. Этап `builder` — создаёт артефакт. Для Python-приложения естественный артефакт —
   виртуальное окружение с зависимостями:

   ```dockerfile
   FROM python:3.12-alpine AS builder
   WORKDIR /build
   COPY app/requirements.txt .
   RUN python -m venv /opt/venv \
       && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
   ```

2. Этап рантайма — забирает только артефакт:

   ```dockerfile
   FROM python:3.12-alpine
   ENV PATH="/opt/venv/bin:$PATH"
   COPY --from=builder /opt/venv /opt/venv
   COPY app/app.py /srv/app/
   ...
   ```

Подсказка: базовые образы обоих этапов должны совпадать по семейству
(в `builder` стоит `alpine` — и в рантайме `alpine`), иначе venv может не запуститься.

Проверь:

```bash
docker build -t lab02:multi .
docker run --rm -d -p 8000:8000 --name lab02 lab02:multi
curl http://localhost:8000/
curl http://localhost:8000/health
docker history lab02:multi   # слоёв из этапа builder в финальном образе нет
```

### Шаг 6. Финальный замер и сводка

```bash
docker images | grep lab02
```

Запиши в заметки таблицу `до / после`: `lab02:before` против финального образа.
Должно получиться уменьшение **в разы** (для полного базового образа — на порядок).

Прогони финальный образ по чек-листу из конспекта ниже — отметь каждый пункт.

### Шаг 7. Убери за собой

```bash
docker rm -f lab02
docker rmi lab02:before lab02:slim lab02:nonroot lab02:health lab02:multi 2>/dev/null
```

Финальный вариант `Dockerfile` оставь в каталоге — он пригодится в следующих лабах.

## Конспект: чек-лист лучших практик

Скопируй к себе в заметки и прогоняй по нему каждый свой Dockerfile:

1. **Минимальный базовый образ** (`-slim` / `alpine`) + тег с версией, а не `latest`.
2. **Кэш-дружелюбный порядок**: редкие изменения (зависимости) — раньше,
   частые (код) — позже.
3. **Зависимости зафиксированы** (`requirements.txt` с `==`).
4. `pip install --no-cache-dir` / `PIP_NO_CACHE_DIR=1` — кэш пакетов в образе не нужен.
5. **Совмещай связанные команды** в один `RUN` через `&&` и убирай мусор там же
   (`rm -rf /var/lib/apt/lists/*` для apt-дистрибутивов): каждый `RUN` — новый слой.
6. **Multi-stage**: в финальном образе только рантайм-артефакты.
7. **Non-root** пользователь: `USER` до `CMD`, файлы приложения принадлежат ему.
8. **HEALTHCHECK** — оркестратор (и `docker`) должен сам видеть, что приложение живо.
9. **Никаких секретов** в `Dockerfile` (ни в `ENV`, ни в `RUN`): они остаются в слоях
   навсегда и видны через `docker history`.
10. `.dockerignore` на месте: в контекст не летят `.git`, `__pycache__`, `.env`.
11. Правильные `ENV` для рантайма (`PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`).
12. `CMD` в exec-форме (`["..."]`), а не в шелл-форме.

## Бонусы (необязательно, но очень учат)

1. **Пин базового образа по digest.** Замени тег на `python:3.12-alpine@sha256:...`
   (digest возьми из `docker inspect --format='{{.RepoDigests}}' ...` или с хаба).
   Что это даёт и когда может мешать?
2. **«Архив с кодом».** Альтернативный вариант multi-stage: на этапе `builder`
   собери артефакт `tar -czf /build/app.tar.gz -C app .`, а в рантайме
   `COPY --from=builder /build/app.tar.gz /tmp/` и распакуй в `WORKDIR`.
   Это минимально допустимая версия задания 5 из плана курса — но вариант с venv полезнее.
3. **Линтер.** Поставь [`hadolint`](https://github.com/hadolint/hadolint) и прогони
   им свой `Dockerfile`: `hadolint Dockerfile`. Почини то, что он найдёт, и объясни
   себе каждое замечание.
4. **Метаданные образа.** Добавь `LABEL org.opencontainers.image.title=...`,
   `org.opencontainers.image.version=...`, `org.opencontainers.image.revision=...`.
   Посмотри их: `docker inspect lab02:multi | grep -A5 Labels`.
5. **Почему не `latest`?** Собери тот же Dockerfile с `python:latest` вместо
   фиксированной версии и сравни размер и поведение. Сформулируй, чем опасен `latest`
   в CI.

## Критерий готовности

- [ ] Новый образ заметно меньше стартового: размеры `до` и `после` записаны в заметки
- [ ] `docker exec lab02 id` показывает, что процесс работает **не** от root
- [ ] Healthcheck работает: `docker inspect --format='{{.State.Health.Status}}' lab02`
      через ~40 секунд показывает `healthy`
- [ ] Финальный `Dockerfile` — многоэтапный (хотя бы два `FROM`, есть `COPY --from=...`)
- [ ] Финальный образ прогнан по чек-листу из конспекта — все 12 пунктов отмечены
- [ ] Отвечены контрольные вопросы ниже

## Контрольные вопросы

1. Почему `python:3.12-alpine` меньше `python:3.12-slim`, а тот меньше `python:3.12`?
   Какой подвох у alpine (подсказка: `musl`, колёса пакетов из PyPI)?
2. В multi-stage сборке зависимости ставятся в `/opt/venv` на этапе `builder`.
   Почему нельзя просто сделать `pip install` в финальном этапе без `--no-cache-dir`,
   и от чего ещё защищает вынос установки в отдельный этап?
3. Что конкретно ограничивает запуск от non-root в случае компрометации приложения?
   Что из привычных действий `appuser` в нашем контейнере сделать уже не сможет?
4. Разбери параметры своего `HEALTHCHECK`: что делают `--interval`, `--timeout`,
   `--start-period`, `--retries`? Через какое **минимальное** время контейнер может
   стать `unhealthy` с твоими настройками?
5. Почему порядок слоёв `зависимости → код` экономит время пересборки, а
   `код → зависимости` — нет? Что произойдёт при изменении `app.py` в каждом случае?
6. Ты видишь в `docker history` слой `RUN pip install` размером 200 МБ, хотя сами
   пакеты весят 20 МБ. Где искать «лишнее» и как этого избежать?
7. Зачем нужны `PYTHONDONTWRITEBYTECODE=1` и `PYTHONUNBUFFERED=1` именно в контейнере?

## Референсное решение

<details>
<summary>Открывай только после того, как сам прошёл все шаги и собрал свой вариант</summary>

Финальный `Dockerfile` (multi-stage, alpine, non-root, healthcheck):

```dockerfile
# Этап 1 — сборочный: ставим зависимости в изолированный venv.
# Всё «тяжёлое» (кэш pip, временные файлы) останется в этом этапе
# и не попадёт в финальный образ.
FROM python:3.12-alpine AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Зависимости копируем отдельно от кода — слой будет переиспользоваться из кэша,
# пока requirements.txt не меняется.
COPY app/requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install -r requirements.txt

# Этап 2 — рантайм: только то, что нужно для запуска приложения.
FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /srv/app

# Готовый venv из сборочного этапа
COPY --from=builder /opt/venv /opt/venv

# Код приложения
COPY app/app.py .

# Отдельный пользователь без прав: компрометация приложения
# не даёт атакующему контроль над контейнером
RUN adduser -D -u 10001 appuser \
    && chown -R appuser /srv/app
USER appuser

EXPOSE 8000

# Проверка живости силами самого Python — curl в alpine не нужен
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

CMD ["python", "app.py"]
```

Быстрая проверка:

```bash
docker build -t lab02:after .
docker run --rm -d -p 8000:8000 --name lab02 lab02:after

curl http://localhost:8000/          # JSON с lab="002-dockerfile-best-practices"
curl http://localhost:8000/health    # {"status": "ok"}

docker exec lab02 id                 # uid=10001(appuser) gid=10001(appuser)
docker inspect --format='{{.State.Health.Status}}' lab02   # через ~40 сек: healthy

docker images | grep lab02           # сравни с lab02:before
docker history lab02:after           # убедись, что «тяжёлых» слоёв из builder нет
```

Ожидаемый порядок цифр (запиши свои реальные значения):

| Образ | Примерный размер |
|-------|------------------|
| `lab02:before` (полный `python:3.12`, как есть) | ~1 ГБ |
| промежуточный вариант на `slim` | ~130–140 МБ |
| `lab02:after` (alpine + multi-stage) | ~55–60 МБ |

Если в лабе 001 ты собирал на `slim`, твой личный выигрыш — с ~130 МБ до ~55 МБ,
и это тоже честно: главное — сам механизм и понимание, откуда берутся мегабайты.

Промежуточный одноэтапный вариант (шаги 2–4 без multi-stage) выглядит так:

```dockerfile
FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/app.py .

RUN adduser -D -u 10001 appuser \
    && chown -R appuser /srv/app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

CMD ["python", "app.py"]
```

</details>

## Если что-то пошло не так

| Симптом | Что проверить |
|---------|---------------|
| `pip install` на alpine падает со сборкой какого-то пакета | Классика `musl` против `glibc`: для пакета нет готового wheel под alpine. В нашей лабе `flask` чистый Python, так что это не должно случиться; в реальных проектах — перейти на `slim` или ставить `build-base` в этапе `builder` |
| `adduser: unknown user` / `useradd: command not found` | Команды создания пользователя разные: в alpine — `adduser -D`, в debian/slim — `useradd`. Проверь, какой у тебя базовый образ |
| Контейнер в статусе `starting` и не становится `healthy` | Проверь `docker inspect lab02 \| grep -A10 Health` — какой вывод у последней проверки. Запусти команду проверки руками: `docker exec lab02 python -c "..."`. Не перепутай порт, `--start-period` ещё не истёк |
| `Permission denied` при старте после `USER appuser` | Файлы приложения принадлежат root: добавь `chown` на каталог с кодом (и на все каталоги, в которые приложение пишет) |
| `venv` из этапа `builder` не работает в рантайме | Базовые образы этапов должны совпадать по семейству и минорной версии Python; `PATH` должен указывать на `/opt/venv/bin` |
| Порт 8000 занят на сервере | `sudo ss -tlnp \| grep 8000` — запусти на другом: `-p 8080:8000` и `curl http://localhost:8080/` |
| `docker images` показывает странные `<none>` образы | Это пересобранные версии старых тегов; почисти: `docker image prune -f` |
