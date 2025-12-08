# Архитектура компонента devices

## Требования
- Создать сущность `Device` (идентификатор, имя, серийный номер, активность, timestamp последнего доступа, ссылка на владельца `user_id`, мета-данные).
- Привязать устройства к новой сущности `Greenhouse`, через которую пользователь организует отдельные теплицы — каждое устройство может принадлежать максимум одной теплице, а каждый пользователь может управлять несколькими теплицами.
- Поддерживать CRUD-операции: регистрация устройства, обновление метаданных, удаление/отвязка.
- Привязка к пользователю: устройство привязывается к `User` в момент создания и может принадлежать только одному владельцу.
- Доступ ограничивается JWT-токеном и зависимостью `get_current_user`; внутри бизнес-логики дополнительно проверяется, что `device.user_id == current_user.id`.

## Backend-слой

### Схемы (Pydantic)
- `DeviceCreate` — обязательные поля `name`, `serial_number`, опционально `config`.
- `DeviceRead` — поля `id`, `name`, `serial_number`, `is_active`, `last_seen`, `user_id` (с `ConfigDict(from_attributes=True)`).
- `DeviceUpdate` — список полей для PATCH/PUT, допускающих изменение имени/метаданных/флага активности.

### Модель (SQLModel)
- `Device` таблица с FK `user_id`, уникальностью `serial_number`, полями `is_active` и `last_seen`.
- Связь с `User` неявно через внешний ключ, но ORM позволяет получать данные владельца, если потребуется.

### Контроллер (`controllers/devices.py`)
- `APIRouter(prefix="/devices", tags=["devices"])`.
- Роуты:
  - `GET /devices` — список устройств текущего пользователя.
  - `POST /devices` — регистрация (проверка уникальности серийника, привязка к `current_user`).
  - `PUT /devices/{device_id}` — обновление (только если владелец).
  - `DELETE /devices/{device_id}` — удаление/отвязка устройства.
- Все маршруты защищены зависимостью `get_current_user`.

### Сервис (`services/devices.py`)
- Бизнес-логика CRUD и проверок:
  - Получение устройства (`get_device_for_user`) и проверка владения.
  - При регистрации выполняется авторизация на ThingsBoard (логин по логину/паролю/`grant_type=password`), полученный токен и проверка, что устройство уже создано на платформе.
  - Создание с хэшированием конфигурации при необходимости и связью с пользователем.
  - Обновление/удаление, возвращающее исключения (`ValueError`) при нарушении правил.

### Интеграция
- Роутер регистрируется из `controllers/__init__.py` вместе с auth/profile.
- При старте `init_db()` создаёт таблицы, добавляя `Device`.
- Конфигурация `Settings` теперь включает `thingsboard_url`, `thingsboard_token` и путь `thingsboard_device_check_path` для проверки, доступных через `.env`.
- JWT и `get_current_user` уже используются: новый контроллер подключает ту же зависимость.

## Frontend-участие
- Главный дашборд дополняется секцией устройств с плитками, показывающими имя, статус (`online`/`offline`) и кнопки “Редактировать”/“Удалить”.
- Кнопка “Добавить устройство” открывает модальное окно или форму:
  - Поля `name`, `serial_number`, необязательный `config`.
  - Отправка `POST /devices` с токеном из `localStorage`/`cookie`.
- Каждая карточка может содержать форму для обновления (`PUT`) и кнопку удаления (`DELETE`).
- Ответы сервера обрабатываются уведомлениями (успех/ошибка). JWT берётся из `login`.
- Статус `is_active` отображается цветом (зелёный для активных, серый — для отключённых).

## Диаграмма взаимодействий

```mermaid
graph LR
  User[User]
  JWT[JWT + OAuth2PasswordBearer]
  AuthRouter[/auth/]
  ProfileRouter[/profile/]
  DevicesRouter[/devices/]
  DevicesService[services devices]
  DeviceModel[models Device]
  UserModel[models User]
  DevicesRouter --> DevicesService
  DevicesService --> DeviceModel
  DevicesService --> UserModel
  JWT --> DevicesRouter
  User --> DevicesRouter
  AuthRouter --> JWT
  ProfileRouter --> User