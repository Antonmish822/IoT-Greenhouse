# Описание проекта growing

## Общая идея

`growing` — минимальный Django-портал управления теплицами с шаблонами для авторизации, дашборда, профиля, уведомлений и работы с устройствами. Сервер отдаёт HTML через стандартный движок Django и не содержит отдельного REST API: все действия организованы через контроллеры приложения `main`.

## Структура

- Конфигурация проекта расположена в [`growing/growing/settings.py`](growing/growing/settings.py:1-126): определены `INSTALLED_APPS`, `MIDDLEWARE`, `DATABASES`, `STATICFILES_DIRS` и другие базовые настройки.
- `growing/manage.py` — утилита управления проектом (миграции, запуск сервера).
- Приложение `main` (`growing/main/`) содержит модели, представления и маршруты:
  - [`growing/main/models.py`](growing/main/models.py:1-8) — простая модель `Telemetry` (название и текст измерения).
  - [`growing/main/views.py`](growing/main/views.py:1-29) — набор функций, возвращающих шаблоны: `login_view`, `dashboard`, `notifications`, `add_device`, `greenhouse_detail`, `profile`, `logout_view`.
  - [`growing/main/urls.py`](growing/main/urls.py:1-12) — маршруты, связывающие URL (`/`, `/dashboard/`, `/notifications/`, `/add_device/`, `/greenhouse_detail/`, `/profile/`, `/logout/`) с соответствующими view.

## Шаблоны и статические ресурсы

- Шаблоны лежат в [`growing/main/templates/main/`](growing/main/templates/main/) и включают `login.html`, `dashboard.html`, `notifications.html`, `add_device.html`, `greenhouse_detail.html`, `profile.html`.
- CSS-файлы (`dashboard.css`, `login.css`, `add_device.css`, `greenhouse-detail.css`, `notifications.css`, `profile.css`) находятся в [`growing/main/static/main/css/`](growing/main/static/main/css/) и подключаются в шаблонах через теги `{% static %}`.
- Путь для статических файлов указывается в [`growing/growing/settings.py`](growing/growing/settings.py:1-126): `STATIC_URL = '/static/'` и `STATICFILES_DIRS = [BASE_DIR / 'main' / 'static']`.

## Запуск и разработка

1. Установите зависимости (например, `pip install django==5.2.8`).
2. Выполните миграции:

```bash
cd growing
python manage.py migrate
```

3. Запустите сервер разработки:

```bash
python manage.py runserver 8010
```

4. Откройте http://127.0.0.1:8010/ — при запросе `/` отображается шаблон логина, остальные страницы доступны по путям из `main/urls.py`.

## Дополнительно

- Проект использует встроенную SQLite-базу (`db.sqlite3`) по адресу `BASE_DIR / 'db.sqlite3'` и стандартный `AUTH_PASSWORD_VALIDATORS` (`settings.py`:85-98).
- Все представления возвращают статические HTML-файлы без обработки POST-запросов; для расширения необходимо добавлять формы и логику сохранения данных.
