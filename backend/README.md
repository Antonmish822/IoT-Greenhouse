# Описание бэкенда Greenhouse

## Общая структура

Сервис реализован на [`FastAPI`](backend/app/main.py:1-32) и `SQLModel`; точка входа в [`backend/app/main.py`](backend/app/main.py:1-32) — инициализация приложения, CORS и регистрация всех маршрутов. Конфигурация (`database_url`, JWT, внешние интеграции) централизована в [`backend/app/config.py`](backend/app/config.py:1-24), а работа с базой происходит через [`backend/app/database.py`](backend/app/database.py:1-16), где создаётся `engine`, вызывается `init_db()` при старте сервиса и реализован генератор сессий `get_session()`.

### Модульные слои

- `controllers/` — роутеры FastAPI, разбитые по доменам (`auth`, `profile`, `devices`, `greenhouses`, `telemetry`). Каждый маршрутизатор инкапсулирует HTTP-обработку и передаёт работу в соответствующие сервисы.
- `services/` — бизнес-логика, которая агрегирует правила и зависимости, проверяет ThingsBoard перед записью устройства и формирует DTO для контроллеров.
- `repositories/` — уровень доступа к данным и CRUD-операции (`devices`, `greenhouses`). Служит абстракцией над сессией SQLModel и обеспечивает проверку уникальности/настройку фильтров.
- `models.py` и `schemas/` — сущности `SQLModel` и `Pydantic` DTO (`User*`, `Device*`, `Telemetry*`, `Greenhouse*`), управляющие сериализацией и валидацией полей.
- `security.py` — JWT-обработка, `OAuth2PasswordBearer`, хэширование паролей и утилиты для `get_current_user`.

## Фичи

### Пользователи

Пользовательская модель описана в [`backend/app/models.py`](backend/app/models.py:5-44) с `email`, `full_name`, хэшированным паролем и флагами активности, подтверждённой регистрации и прав доступа. DTO (`UserCreate`, `UserRead`, `UserUpdate`) расположены в [`backend/app/schemas/user.py`](backend/app/schemas/user.py:1-45).

### Аутентификация и авторизация

- Пароли хэшируются через `passlib`/`bcrypt`, конфигурируется в [`backend/app/security.py`](backend/app/security.py:1-40).
- JWT подписываются и проверяются с помощью `python-jose`, параметры (`secret`, `algorithm`, `expire_minutes`) — в настройках.
- Защита приватных маршрутов происходит через зависимость `get_current_user`, которая декодирует токен и подгружает пользователя.

### Устройства и телеметрия

- `Device` содержит `device_metadata`, сохраняемое как JSON-колонка `metadata`, чтобы избежать конфликтов с `SQLAlchemy.MetaData` (описание в [`backend/app/models.py`](backend/app/models.py:21-50)).
- DTO `DeviceCreate`, `DeviceRead`, `DeviceUpdate` лежат в [`backend/app/schemas/device.py`](backend/app/schemas/device.py:1-70) и поддерживают клиентские псевдонимы.
- Сервисы устройств (`backend/app/services/devices.py`:1-130) валидируют уникальность `serial_number`, взаимодействуют с ThingsBoard (`_verify_device_on_thingsboard`, `_get_thingsboard_token`) и сохраняют изменённые поля.
- Телеметрия (`backend/app/services/telemetry.py`:1-90) агрегирует данные и отдаёт их через контроллеры, включая временные ряды и фильтрацию.

### Зеленые дома

Контроллеры `greenhouses`, `telemetry` и `devices` позволяют управлять объектами, искать устройства по `greenhouse_id` и получать статистику по показателям климата. Модели/схемы для `Greenhouse` находятся в [`backend/app/schemas/greenhouse.py`](backend/app/schemas/greenhouse.py:1-80).

## Запуск

1. Установите зависимости из `requirements.txt`.
2. Создайте `.env`, если нужна кастомизация (см. `Settings` в [`backend/app/config.py`](backend/app/config.py:1-24)).
3. Запустите команду:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8001
```

Сервис станет доступен по `http://127.0.0.1:8000`, документация автоматически публикуется на `/docs` и `/redoc`.

## Конфигурация и безопасность

- Переменные JWT (`jwt_secret`, `jwt_algorithm`, срок токена), параметры базы `database_url` и ThingsBoard (`thingsboard_url`, пути, логин/пароль/токен) задаются через `Settings`.
- Для разработки можно подготовить `.env`, а в продакшене обязательно сменить `jwt_secret` на безопасный ключ и при необходимости разграничить среды через дополнительные файлы конфигурации.
- Для корректной работы ThingsBoard необходимо задать `thingsboard_url`, `thingsboard_username` и `thingsboard_password`, либо поставить статический `thingsboard_token`.

### Переменные окружения

Файл [`.env`](.env:1-15) наполняет поля конфигурации [`Settings`](backend/app/config.py:1-24). Ключевые переменные:

- `APP_NAME` — заголовок FastAPI и отображаемое имя сервиса.
- `DATABASE_URL` — путь к базе (`sqlite:///./backend/dev.db` по умолчанию).
- `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` — параметры генерации JWT-токенов.
- `FRONTEND_ALLOWED_ORIGIN` — разрешённый origin для CORS, используемый в [`backend/app/main.py`](backend/app/main.py:1-32).
- `THINGSBOARD_URL`, `THINGSBOARD_USERNAME`, `THINGSBOARD_PASSWORD` — адрес и учётные данные ThingsBoard; вместо пары логин/пароль можно задать `THINGSBOARD_TOKEN`.
- `THINGSBOARD_LOGIN_PATH`, `THINGSBOARD_DEVICE_CHECK_PATH`, `THINGSBOARD_TELEMETRY_PATH` — относительные пути для авторизации, проверки устройств и телеметрии.
- `THINGSBOARD_REQUEST_TIMEOUT`, `THINGSBOARD_TELEMETRY_KEYS`, `THINGSBOARD_TELEMETRY_LIMIT` — параметры таймаута и объёма телеметрии при запросах.
