# docker-labs: практический курс и production-ready сценарии

Практический курс и готовые решения: от базовых Dockerfile до production-ready стандартов, Docker Compose, CI/CD и безопасности.

Формат: работа в терминале на реальном сервере, выполнение конкретных прикладных задач. Каждый шаг проверяется по объективным критериям и метрикам.

Курс покрывает путь: **Docker → Docker Compose → CI/CD (GitHub Actions) → деплой на VPS → безопасность**.

## Программа курса

8 лабораторных, выполняются **строго по порядку** — каждая опирается на предыдущую.
Подробный план с целями, заданиями и критериями завершения: [docs/plan.md](docs/plan.md).

| # | Лабораторная | Тема | Что получилось в итоге |
|---|--------------|------|------------------------|
| 1 | [001-first-dockerfile](labs/001-first-dockerfile/) ✅ | Первый Dockerfile | Чистый образ Flask (python:3.12-slim), кэширование слоев (equirements.txt до кода), exec-форма CMD для корректной обработки сигналов OS (PID 1). Сборка на удаленном сервере. |
| 2 | [002-dockerfile-best-practices](labs/002-dockerfile-best-practices/) ✅ | Лучшие практики Dockerfile | **Multi-stage сборка** на Alpine: сборочный venv перенесен в минимальный рантайм. Запуск под **non-root пользователем** (\ppuser\, UID 10001). Нативный **HEALTHCHECK** на Python (\urllib.request\). Сжатие размера **с 1.62 ГБ до 98.8 МБ** (в 16.4 раза!). |
| 3 | 🚧 003-docker-compose | Docker Compose | Мультисервисный проект одной командой: сети, томы, nginx |
| 4 | 🚧 004-registry-and-debugging | Регистры и отладка | Образ в GHCR, \docker logs\ / \exec\ / \inspect\ как инструменты |
| 5 | 🚧 005-ci-github-actions | CI: GitHub Actions | На каждый push в ветку собирается образ в CI |
| 6 | 🚧 006-cd-deploy-vps | CD: деплой на VPS | После push обновлённое приложение само заводится на сервере |
| 7 | 🚧 007-security | Безопасность | Trivy-скан образов, секреты, non-root, патчинг базовых образов |
| 8 | 🚧 008-final-project | Финальный проект | Проект с БД, CI и CD, заведённый с чистого сервера |

✅ — лабораторная готова и выполнена, 🚧 — в плане.

## Как работать

1. **Склонируй репозиторий на сервер** (или локально):

   \\\ash
   git clone https://github.com/Anx28/docker-labs.git
   cd docker-labs
   \\\

2. **Открой лабораторную**: \cd labs/001-first-dockerfile\ и изучи её \README.md\.
   Внутри: цель → требования → пошаговая инструкция → проверка результата → контрольные вопросы.

3. **Выполняй в терминале в каталоге лабораторной.** Код приложения лежит в каталоге \pp/\ — пиши и оптимизируй манифесты сам.

4. **Проверь результат** по списку критериев, замерам метрик (размер, healthcheck, non-root) и контрольным вопросам.

> Референсные решения спрятаны в сворачиваемом блоке \<details>\ в README лабораторной.

## Базовые требования

- Linux-сервер (Ubuntu 22.04+ или Debian 12+) с доступом по SSH
- **Docker Engine 24+**
- **git**
- **curl**

Быстрая самопроверка окружения:

\\\ash
git --version
docker --version
docker run --rm hello-world
\\\

## Структура репозитория

\\\
docker-labs/
├── README.md                        # этот файл
├── docs/
│   └── plan.md                      # полный план курса (8 лабораторных)
└── labs/
    ├── 001-first-dockerfile/        # Лаба 001: базовый Dockerfile, кэширование слоев
    │   ├── README.md
    │   ├── Dockerfile
    │   ├── .dockerignore
    │   └── app/
    └── 002-dockerfile-best-practices/ # Лаба 002: multi-stage, non-root, healthcheck
        ├── README.md
        ├── Dockerfile
        ├── .dockerignore
        └── app/
\\\
