# 🌱 Умная теплица

Всё про IoT-экосистему автоматизированного проветривания теплиц: фронтенд, FastAPI-бэкенд и Django-панель. Проект включает документированные сервисы, готовую инфраструктуру и простые шаблоны для управления микроклиматом.

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

---

## 💻 Как запускать

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8001
```

Документация доступна на `/docs` и `/redoc` при поднятом бэкенде. Создайте `.env` по примеру (см. [`backend/app/config.py`](backend/app/config.py:1-24) и `backend/README.md`).

### Django-панель

```bash
cd growing
python -m venv .venv
source .venv/bin/activate
pip install Django==5.2.8
python manage.py migrate
python manage.py runserver 8010 
```

Доступ по умолчанию `http://127.0.0.1:8010/` (страница логина из `growing/main/templates/main/login.html`).

---

## 🧪 Разработка и вклад

- В `backend/` добавляйте сервисы, контроллеры и схемы согласно архитектуре FastAPI/SQLModel; сервисы описаны в `backend/app/services`, контроллеры в `backend/app/controllers`.
- Развивайте Django-часть через `growing/main/views.py` и шаблоны, а новые стили — в `growing/main/static/main/css/`.
- Документируйте сложные изменения в `docs/` (AsciiDoc и yaml). Pull Request'ы приветствуются.

---

## ⚖️ Лицензия

Проект распространяется под лицензией **[MIT](LICENSE)**.

---

## 👥 Авторы и идея

Для дачников и фермеров: прозрачно соединённый стек (FastAPI + Django + чистый фронтенд) делает автоматизацию теплиц понятной и расширяемой.
