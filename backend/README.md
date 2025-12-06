# Описание бэкенда Greenhouse

## Общая структура

Бэкенд реализован с использованием [`FastAPI`](backend/app/main.py:1-118) и `SQLModel` для работы с объектами и базой данных. Приложение поднимает API-сервер, в котором описаны аутентификация пользователей, управление профилем и работа с токенами доступа. Настройки хранятся в [`backend/app/config.py`](backend/app/config.py:1-9), включая параметры базы данных и JWT.

### Модульная организация

- `controllers/` — FastAPI-роутеры по доменам (`auth`, `profile` и компоненты `devices`, `telemetry`, `notifications`). Отвечают за HTTP-интерфейс и делегируют работу в сервисы.
- `services/` — бизнес-логика, инкапсулирующая взаимодействие с репозиториями, правила обработки данных и формирование результатов.
- `repositories/` — низкоуровневый доступ к данным и CRUD-операции, например [`backend/app/repositories/devices.py`](backend/app/repositories/devices.py:1-57).
- `security.py` — JWT, `OAuth2PasswordBearer`, хэширование паролей и зависимость `get_current_user`.
- `database.py` — создание `engine`, инициализация `SQLModel` и генератор сессий `get_session`.
- `models.py`, `schemas.py` — описанные через `SQLModel` и `Pydantic` сущности для CRUD и DTO.
- `config.py` — настройки через `pydantic_settings`, включая секреты, URL базы и параметры ThingsBoard.
- `controllers/__init__.py` — агрегирует роутеры для единой регистрации в `main.py`.

Новая структура позволяет добавлять компоненты путём создания новых контроллеров и сервисов без модификации существующих слоёв.

## Функциональные возможности

### Пользователи

- Сущность пользователя описана в [`backend/app/models.py`](backend/app/models.py:6-11) и включает уникальный email, имя (`full_name`), хэшированный пароль и флаг активности.
- Валидация входных/выходных DTO реализована в [`backend/app/schemas.py`](backend/app/schemas.py:6-21) через `pydantic` модели `UserCreate`, `UserRead` и `UserUpdate`.

### Аутентификация и авторизация

- Пароли хэшируются и сравниваются с помощью [`passlib`](backend/app/security.py:5-25), настроенного через `bcrypt`.
- JWT-токены создаются и декодируются с помощью `python-jose` и используют секрет, алгоритм и время жизни из настроек.
- Токен используется в зависимости `OAuth2PasswordBearer` для защиты приватных маршрутов.

### Эндпоинты

Сервер предоставляет следующие ключевые маршруты:
1. `/auth/register` — регистрация нового пользователя с хэшированием пароля и созданием записи в БД.
2. `/auth/login` — проверка email/пароля, генерация JWT и возврат `UserRead`.
3. `/profile` (GET/PUT) — получение и обновление профиля авторизованного пользователя, включая смену имени и пароля.
4. `/devices` — CRUD для устройств: контроллер [`backend/app/controllers/devices.py`](backend/app/controllers/devices.py:1-67) работает через сервис [`backend/app/services/devices.py`](backend/app/services/devices.py:1-123) и репозиторий [`backend/app/repositories/devices.py`](backend/app/repositories/devices.py:1-57).
5. Все приватные маршруты защищены зависимостью `get_current_user`, которая декодирует токен и ищет пользователя в базе.

### Устройства

- `Device` описана в [`backend/app/models.py`](backend/app/models.py:21-32) с полем `device_metadata`, мапящимся на колонку `metadata`, чтобы избежать конфликта с системным `SQLAlchemy.MetaData`.
- DTO для устройств (`DeviceCreate`, `DeviceRead`, `DeviceUpdate`) находятся в [`backend/app/schemas/device.py`](backend/app/schemas/device.py:1-68) и поддерживают псевдоним `metadata`, используемый клиентом API.
- Сервис [`backend/app/services/devices.py`](backend/app/services/devices.py:1-123) использует `[persistence logic](backend/app/repositories/devices.py:1-57)`, валидирует уникальность `serial_number`, а перед сохранением проверяет устройство на существование в ThingsBoard (`_verify_device_on_thingsboard` и `_get_thingsboard_token`).
- Метаданные устройства сохраняются как JSON через `device_metadata`, при обновлениях сервис сохраняет только изменённые поля.

### База данных и миграции

- Создание базы и таблиц происходит при старте сервиса в `on_startup`, вызывающем [`init_db`](backend/app/database.py:10-16).
- Сессии к базе открываются с помощью генератора `get_session`, предоставляемого через зависимости FastAPI.

## Как запустить

1. Установить зависимости из `requirements.txt`.
2. Обеспечить наличие файла SQLite `backend/dev.db` (создаётся автоматически при первом старте).
3. Запустить приложение командой `uvicorn backend.app.main:app --reload`.

В результате сервис будет доступен по адресу `http://127.0.0.1:8000`, а схема API автоматически выставляется по `/docs` и `/redoc`.

## Безопасность и конфигурацию

- Параметры JWT (`jwt_secret`, `jwt_algorithm`, срок жизни), база данных и ThingsBoard (`thingsboard_url`, `thingsboard_login_path`, `thingsboard_device_check_path`, `thingsboard_username`, `thingsboard_password`, `thingsboard_token`) настраиваются в [`backend/app/config.py`](backend/app/config.py:1-19). Для разработки можно скопировать шаблон `.env-sample`, где описаны все переменные.
- Хэширование паролей выполняется через `bcrypt`, а секретный ключ должен быть заменён на безопасное значение перед продом.
- При необходимости можно адаптировать `access_token_expire_minutes` и `database_url` для разных окружений. Для проверки устройств ThingsBoard нужно обеспечить корректные URL и логин/пароль, либо задать статический `thingsboard_token`.