# Лабораторная 003 — Docker Compose: мультисервисный стек

## Цель

Собрать и запустить полноценный production-подобный мультисервисный проект одной командой:
**Flask-приложение (из лабы 002) + Nginx в роли reverse-proxy**.

После этой лабораторной ты научишься:
- связывать сервисы через пользовательские сети Docker и встроенный Service Discovery (DNS);
- изолировать бэкенд от внешнего мира (доступ только через reverse-proxy);
- синхронизировать запуск сервисов через `depends_on` с проверкой `condition: service_healthy`;
- сохранять логи и данные через именованные тома (Volumes);
- управлять конфигурацией через переменные окружения (`.env`).

---

## Требования к окружению

- Сервер со стендом (`spechive` **78.40.198.168** через `docker context use spechive`).
- **Docker Compose v2** (проверка: `docker compose version`).

> ⚠️ **Боевая деталь хоста:**
> На нашем сервере `spechive` порты `80` и `443` уже заняты системным Nginx хоста (мы проверили через `ss -tulpn`).
> Поэтому внешний порт для контейнера Nginx вынесен в `.env` (`NGINX_PORT=8088`), а внутри контейнера Nginx слушает стандартный `80`.
> Это частая реальная ситуация: на одном сервере запускается несколько проектов, и порты хоста нужно разводить через переменные.

---

## Что уже есть в каталоге лабораторной

| Файл | Назначение |
|---|---|
| `app/` | Готовое Flask-приложение и проверенный multi-stage `Dockerfile` из лабы 002 |
| `nginx/default.conf` | Конфигурация Nginx: проксирование запросов на `http://app:8000` |
| `.env.example` | Пример файла переменных окружения с портом `NGINX_PORT=8088` |
| `.gitignore` | Исключает секреты (`.env`) и временные файлы Python из git |

---

## Задание

### Шаг 1. Подготовь `.env` файл

Скопируй шаблон в рабочий `.env`:

```bash
cp .env.example .env
```

Посмотри его содержимое. Значение `NGINX_PORT=8088` будет подставлено в `docker-compose.yml`.

---

### Шаг 2. Напиши `docker-compose.yml`

Создай файл `docker-compose.yml` в корне каталога `labs/003-docker-compose/`:

```bash
touch docker-compose.yml
```

Требования к структуре:

1. **Сервис `app` (бэкенд):**
   - собирается из каталога `./app` (директива `build: ./app`);
   - перезапуск при сбоях: `restart: unless-stopped`;
   - **НЕ публикует порт наружу** — используется `expose: ["8000"]` (порт доступен только внутри сети Docker);
   - подключен к сети `backend`;
   - передает переменную окружения `APP_ENV=${APP_ENV}`.

2. **Сервис `web` (reverse-proxy Nginx):**
   - образ: `nginx:1.27-alpine`;
   - перезапуск: `restart: unless-stopped`;
   - публикует порт на хост: `ports: ["${NGINX_PORT:-8088}:80"]`;
   - монтирует два тома:
     - `./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro` (bind mount конфига, только для чтения);
     - `nginx_logs:/var/log/nginx` (именованный том для логов Nginx);
   - подключен к сети `backend`;
   - **зависит от `app`:** запускается только тогда, когда `app` успешно прошел проверку здоровья:
     ```yaml
     depends_on:
       app:
         condition: service_healthy
     ```

3. **Секция `networks`:**
   - объявляет сеть `backend` (с драйвером `bridge`).

4. **Секция `volumes`:**
   - объявляет именованный том `nginx_logs`.

---

### Шаг 3. Собери и запусти стек

Запусти сборку и старт сервисов в фоновом режиме:

```bash
docker compose up -d --build
```

Обрати внимание на вывод: Docker Compose сначала соберет образ `app`, запустит его, дождется статуса `healthy`, и только после этого поднимет контейнер `web`!

---

### Шаг 4. Проверь работу и изоляцию

1. **Проверь статус сервисов:**
   ```bash
   docker compose ps
   ```
   Оба контейнера должны быть в статусе `Up`, при этом у `app` должно быть `(healthy)`.

2. **Проверь доступ через Nginx:**
   ```bash
   ssh spechive curl -s http://localhost:8088/
   ssh spechive curl -s http://localhost:8088/health
   ```
   Ответ должен прийти от Flask через Nginx.

3. **Проверь изоляцию сети (бэкенд скрыт!):**
   Попробуй обратиться напрямую к Flask на 8000 порт:
   ```bash
   ssh spechive curl http://localhost:8000/
   ```
   Должен вернуться отказ соединения (*Connection refused*), так как порт 8000 наружу не проброшен!

4. **Проверь логи Nginx в томе:**
   ```bash
   docker compose logs web
   docker volume inspect 003-docker-compose_nginx_logs
   ```

---

### Шаг 5. Проверь сохранение данных (жизненный цикл)

Останови стек:
```bash
docker compose down
```
Затем подними снова:
```bash
docker compose up -d
```
Убедись, что логи в томе не потерялись:
```bash
docker compose logs web
```

---

## Критерий готовности

- [ ] Создан и настроен `.env` файл
- [ ] Написан `docker-compose.yml` с сервисами `app` и `web`
- [ ] `docker compose up -d --build` поднимает стек без ошибок
- [ ] Nginx ждет готовности Flask через `condition: service_healthy`
- [ ] Запросы успешно проходят через Nginx на порту `8088`
- [ ] Порт `8000` приложения недоступен снаружи хоста
- [ ] Логи Nginx сохраняются в именованном томе `nginx_logs`
- [ ] Отвечены контрольные вопросы ниже

---

## Контрольные вопросы

1. В чем разница между директивами `ports` и `expose` в `docker-compose.yml`? Почему бэкенду нужен только `expose`?
2. Как Nginx узнает IP-адрес сервиса `app` по имени `http://app:8000`? Какой компонент Docker отвечает за это имя?
3. Чем `depends_on: ... condition: service_healthy` принципиально отличается от обычного `depends_on: [app]`? Что происходит при обычном `depends_on`, если приложение долго стартует?
4. В чем разница между bind mount (`./nginx/default.conf:...`) и именованным томом (`nginx_logs:...`)? В каких сценариях используется каждый из них?
5. Зачем при монтировании конфига Nginx добавлен флаг `:ro` (`read-only`)?
6. Что делает флаг `-v` при выполнении `docker compose down -v`?

---

## Референсное решение

<details>
<summary>Открывай только после того, как сам написал и запустил docker-compose.yml</summary>

```yaml
services:
  app:
    build:
      context: ./app
      dockerfile: Dockerfile
    restart: unless-stopped
    expose:
      - "8000"
    environment:
      - APP_ENV=${APP_ENV:-production}
    networks:
      - backend

  web:
    image: nginx:1.27-alpine
    restart: unless-stopped
    ports:
      - "${NGINX_PORT:-8088}:80"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - nginx_logs:/var/log/nginx
    depends_on:
      app:
        condition: service_healthy
    networks:
      - backend

networks:
  backend:
    driver: bridge

volumes:
  nginx_logs:
```

</details>
