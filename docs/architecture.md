# Архитектура проекта Smart Greenhouse Backend

## Общее описание

Backend системы Smart Greenhouse построен на фреймворке FastAPI с использованием SQLite в качестве базы данных. Архитектура следует принципам REST API и разделения на слои.

## Структура проекта

```
backend/
├── main.py                 # Точка входа приложения
├── requirements.txt       # Зависимости проекта
├── app/                    # Основное приложение
│   ├── __init__.py
│   ├── database.py         # Конфигурация базы данных
│   ├── models/             # Модели данных SQLAlchemy
│   │   ├── __init__.py
│   │   ├── user.py         # Модель пользователя
│   │   ├── device.py       # Модель устройства
│   │   └── notification.py  # Модели уведомлений
│   ├── schemas/            # Pydantic схемы
│   │   ├── __init__.py
│   │   ├── user.py         # Схемы для пользователей
│   │   ├── device.py       # Схемы для устройств
│   │   └── notification.py  # Схемы для уведомлений
│   └── api/                # API роутеры
│       ├── __init__.py
│       ├── auth.py          # Аутентификация
│       ├── devices.py       # Управление устройствами
│       ├── telemetry.py     # Телеметрия
│       ├── notifications.py # Уведомления
│       └── frontend.py     # Эндпоинты для фронтенда
```

## Компоненты системы

### 1. Модели данных (models/)

Реализованы следующие модели SQLAlchemy:
- `User` - Пользователь системы
- `Device` - Устройство теплицы
- `Notification` - Уведомление
- `NotificationSettings` - Настройки уведомлений

### 2. Схемы данных (schemas/)

Pydantic схемы для валидации данных:
- `User` - Схемы для пользователей
- `Device` - Схемы для устройств
- `Notification` - Схемы для уведомлений

### 3. API эндпоинты (api/)

#### Аутентификация (/auth)
- `POST /register` - Регистрация нового пользователя
- `POST /login` - Вход в систему

#### Устройства (/devices)
- `GET /` - Получить список устройств пользователя
- `POST /` - Добавить новое устройство
- `GET /{deviceId}` - Получить информацию об устройстве
- `PUT /{deviceId}` - Обновить настройки устройства
- `DELETE /{deviceId}` - Удалить устройство
- `POST /{deviceId}/control` - Управление устройством вручную

#### Телеметрия (/telemetry)
- `GET /{deviceId}` - Получить телеметрию устройства
- `GET /{deviceId}/current` - Получить текущие показания датчиков

#### План добавления контроллера `/telemetry/{deviceId}` (без сохранения данных)
1. **Маршрут** — FastAPI-роутер в `controllers/telemetry.py` с prefix `/telemetry`, принимающий `POST` или `PUT` (по договорённости) пакет с `deviceId`, `timestamp`, `payload`. Роутер использует зависимость `get_current_user` и `get_session`, извлекает устройство через `devices.get_device_for_user` и возвращает `404`, если нет привязки.
2. **Сервис** — промежуточный модуль `services/telemetry.py`, получающий пакет DTO (`TelemetryPacket`) без сохранения в БД. Сервис выполняет минимальную валидацию (`device_id`, `payload`, `rum`) и делегирует пересылку.
3. **Gateway** — адаптер `telemetry/thingsboard.py` (или `telemetry/broadcast.py`) с интерфейсом `push(device, packet)` и реализацией REST-запроса в ThingsBoard ({apply existing `_get_thingsboard_token`}) или WebSocket-рассылки клиентам.
4. **Конфигурация** — расширить [`Settings`](backend/app/config.py:1-19) переменными `telemetry_mode`, `telemetry_ws_path`, `telemetry_thingsboard_topic`.
5. **Документация** — раздел описывает, что данные не сохраняются, а транслируются напрямую через ThingsBoard/API/WebSocket, и объясняет, как фронтенд или другие сервисы подписываются на обновления (`/telemetry/{deviceId}` → сервис → gateway).

#### Уведомления (/notifications)
- `GET /` - Получить историю уведомлений
- `GET /settings` - Получить настройки уведомлений
- `PUT /settings` - Обновить настройки уведомлений

#### Фронтенд (/frontend)
- `GET /dashboard` - Данные для главной страницы
- `GET /device/{deviceId}/page` - Данные для страницы устройства

## База данных

Используется SQLite для хранения данных:
- Таблица `users` - Пользователи
- Таблица `devices` - Устройства
- Таблица `notifications` - Уведомления
- Таблица `notification_settings` - Настройки уведомлений

## Зависимости

Основные зависимости проекта:
- `fastapi` - Веб-фреймворк
- `uvicorn` - ASGI сервер
- `sqlalchemy` - ORM для работы с базой данных
- `pydantic` - Валидация данных
- `python-jose` - Работа с JWT токенами
- `passlib` - Хэширование паролей

## Запуск проекта

1. Установка зависимостей:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. Запуск сервера:
   ```bash
   uvicorn backend.main:app --reload
   ```

3. Доступ к API:
   - Локальный сервер: http://localhost:8000
   - Документация API: http://localhost:8000/docs