# 🌱 Умная теплица

Всё про IoT-экосистему автоматизированного проветривания теплиц: фронтенд, FastAPI-бэкенд и Django-панель. Проект включает документированные сервисы, готовую инфраструктуру и простые шаблоны для управления микроклиматом.

---

## 🚀 Статус Проекта и Ветвление

Эта ветка (`dev-automation`) является новой стабильной базой для проекта. Ветка `main` будет синхронизирована с этой веткой. Мы активно развиваем проект и приветствуем новых контрибьюторов! Пожалуйста, ознакомьтесь с [CONTRIBUTING.md](CONTRIBUTING.md) для получения подробных инструкций по участию.

---

## 📌 Состав проекта

- [`backend/`](backend/README.md:1) — сервис на FastAPI/SQLModel с JWT, ThingsBoard-интеграцией и полным описанием маршрутов, моделей, зависимостей и переменных окружения с примерами (`backend/README.md`).
- [`growing/`](growing/README.md:1) — шаблонное Django-приложение `main` с простыми представлениями, страницами (включая логин, дашборд, уведомления, добавление устройств) и статикой, описанное в [`growing/README.md`](growing/README.md:1).
- [`docs/`](docs/index.adoc:1) — документация AsciiDoc и диаграммы, включая OpenAPI (`docs/swagger/IoT_Greenhouse.yaml`).
- [`frontend/`](frontend/architecture.md:1) — прототипы и черновики интерфейсов (актуальный фронтенд оформляется в этом каталоге).

---

## 🎯 Возможности всего решения

- **Backend (FastAPI)**: JWT-аутентификация, CRUD-операции по пользователям, устройствам и теплицам, ThingsBoard-проверка устройств, телеметрия и SQLModel-сессии (описание — [`backend/README.md`](backend/README.md:1-60)).
- **Django-управление**: простые шаблонные страницы (логин, табло, профиль, уведомления и др.), маршруты в `growing/main/urls.py` и статическое оформление (`growing/main/static/main/css/`) — см. [`growing/README.md`](growing/README.md:1-17).
- **Документация**: архитектура и ERD-диаграммы в `docs/`, OpenAPI-спецификация для бэкенда.
- **Автоматизация температуры**: В рамках `dev-automation` была реализована первая версия автоматического управления температурой, включая API и логику для контроля приводов.

---

## 💻 Как запускать

### Рекомендуемый способ: Docker Compose

Наиболее простой и рекомендуемый способ запустить весь проект локально:

```bash
docker compose up --build -d
```

Эта команда:
- Пересобирает Docker-образы для бэкенда, фронтенда и nginx.
- Запускает три контейнера в фоновом режиме:
    - `backend` (FastAPI): Доступен внутри Docker по порту `8001`.
    - `frontend` (Django): Доступен внутри Docker по порту `8010`.
    - `nginx`: Слушает порты `80` (HTTP) и `443` (HTTPS) на вашей хост-машине и проксирует запросы:
        - `/api/` на `backend`.
        - Все остальные пути на `frontend`.

После запуска вы можете получить доступ к фронтенду, открыв ваш веб-браузер по адресу: `http://localhost`

**Важно:** Для корректной работы убедитесь, что в `frontend/.env` заданы `BACKEND_URL=http://iotgreenhouse.ru/api` и `ALLOWED_HOSTS` включает `iotgreenhouse.ru`, а домен `iotgreenhouse.ru` резолвится на хост с контейнерами (или настройте локальный DNS, например, через `/etc/hosts`).

### Backend (вручную, для разработки)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8001
```

Документация API доступна по адресу `http://localhost:8001/docs` и `http://localhost:8001/redoc` при поднятом бэкенде. Создайте файл `.env` по примеру (см. [`backend/.env.example`](backend/.env.example) и `backend/README.md`).

### Django-панель (вручную, для разработки)

```bash
cd frontend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt # Вместо `pip install Django==5.2.8`
python manage.py migrate
python manage.py runserver 0.0.0.0:8010 # Changed to 0.0.0.0 for consistency
```

Доступ по умолчанию `http://127.0.0.1:8010/` (страница логина из `frontend/main/templates/main/login.html`).

### SSL-сертификат iotgreenhouse.ru
1. Убедитесь, что домен `iotgreenhouse.ru` резолвится на ваш хост и что порты 80 и 443 свободны. При необходимости остановите уже работающие сервисы (например, системный `nginx`).
2. Получите сертификат с помощью `certbot` (standalone). Пример команды:
   ```bash
   sudo certbot certonly --standalone -d iotgreenhouse.ru --agree-tos --email admin@iotgreenhouse.ru
   ```
3. Скопируйте и переименуйте сертификат и ключ в проект:
   ```bash
   mkdir -p nginx/certs
   sudo cp /etc/letsencrypt/live/iotgreenhouse.ru/fullchain.pem nginx/certs/iotgreenhouse.crt
   sudo cp /etc/letsencrypt/live/iotgreenhouse.ru/privkey.pem nginx/certs/iotgreenhouse.key
   sudo chown $(id -u):$(id -g) nginx/certs/*
   ```
4. Перезапустите контейнеры:
   ```bash
   docker compose up -d --build
   ```
   При обновлении сертификата (`certbot renew`) повторите копирование и перезапуск.

---

## 🧪 Разработка и вклад

Мы приветствуем ваш вклад в развитие проекта! Для того чтобы ваша работа была эффективной и соответствовала нашим стандартам, пожалуйста, ознакомьтесь с [CONTRIBUTING.md](CONTRIBUTING.md).

Краткие рекомендации:
-   **Ветвление:** Используйте [Feature Branch Workflow](#) (создавайте отдельные ветки для каждой новой функции или исправления).
-   **Качество кода:** Мы используем `Black` для форматирования, `Flake8` для линтинга и `pre-commit` хуки для автоматической проверки кода перед коммитом. Установите их перед началом работы (`pre-commit install`).
-   **Тестирование:** Пишите тесты для нового функционала.
-   **Документация:** Обновляйте соответствующую документацию (`README.md`, `docs/`) по мере необходимости.

---

## ⚖️ Лицензия

Проект распространяется под лицензией **[MIT](LICENSE)**.

---

## 👥 Авторы и идея

Для дачников и фермеров: прозрачно соединённый стек (FastAPI + Django + чистый фронтенд) делает автоматизацию теплиц понятной и расширяемой.
