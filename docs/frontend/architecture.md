# Django-фронтенд для IoT-Greenhouse

## 1. Общая идея
Django-приложение выступает клиентом FastAPI, используя JWT-авторизацию для работы с `/auth/*`, `/devices`, `/telemetry`, `/notifications` и `/devices/{id}/control`. Интерфейс реализован через отдельные шаблоны (login, dashboard, greenhouse-detail, notifications, add-device) и связывается с backend через сервисный слой (HTTP-клиенты).

## 2. Структура приложений
- `core` (или `frontend`) — базовые страницы и маршруты (`/`, `/dashboard`, `/greenhouse/<id>`, `/notifications`), обработка JWT-сессии, контекстные процессоры.
- `accounts` — формы входа/регистрации, JWT-хранение в cookie/localStorage, middleware для защиты.
- `devices` — управление устройствами (список, подключение, управление приводом). Использует сервисы, делающие запросы к FastAPI.
- `telemetry` — получение телеметрии через `/telemetry/{device_id}` и формирование графиков (например, Chart.js на клиенте или готовые JSON-данные).
- `notifications` — просмотр истории уведомлений и настроек (GET/PUT).
- `integrations` — адаптеры ThingsBoard (если нужно) и websocket-клиенты (SSE/Channels) для «живых» обновлений.

## 3. Шаблоны и компоненты
- `base.html`: общий layout (sidebar, header, user menu, notifications badge).
- `login.html`: форма входа/регистрации; при submit — POST `/auth/login` → сохраняем JWT; настраиваем redirect.
- `dashboard.html`: карточки теплиц, данные из `GET /devices`, кнопка добавить устройство (modal/form).
- `greenhouse_detail.html`: текущие показатели, графики, управление приводом (отправка POST/PUT `/devices/{id}/control`), отображение телеметрии (fetch `/telemetry/{id}`).
- `notifications.html`: история и настройки (GET/PUT `/notifications`, `/notifications/settings`).

## 4. Сервисный слой (Django)
Каждое приложение использует `services/api_client.py`:
```python
class FastAPIClient:
    def __init__(self, token: str | None):
        self.base = settings.BACKEND_URL
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def get(self, path, params=None):
        return httpx.get(f"{self.base}{path}", headers=self.headers, params=params, timeout=5)

    def post(self, path, data=None):
        return httpx.post(...)

    ...
```
Контроллеры/представления вызывают `client.get("/devices")`, `client.get(f"/telemetry/{device_id}")`, `client.put(f"/devices/{id}/control", json=payload)`.

## 5. Поток данных
1. **Аутентификация** — пользователь вводит email/пароль → `POST /auth/login`; JWT сохраняется в cookie `access_token`.
2. **Dashboard** — `FastAPIClient.get("/devices")`; ответ рендерится в шаблоне, дополняется статусами и кнопками перехода к `greenhouse/<id>`.
3. **Детальный вид теплицы** — при заходе делаем параллельные запросы:
   - `GET /devices/{id}` для метаданных.
   - `GET /telemetry/{id}` для телеметрии; данные сериализуются в JSON (для Chart.js).
4. **Управление приводом** — из формы отправляется `PUT /devices/{id}` или `POST /devices/{id}/control`.
5. **Уведомления** — `GET /notifications`, `GET /notifications/settings`, `PUT /notifications/settings`.
6. **Добавление устройства** — форма `Device ID + Access Token` → `POST /devices`.
7. **ThingsBoard** — backend сам запрашивает `/telemetry/{device_id}`; фронтенд только отображает уже собранные данные.

## 6. Аутентификация и хранение
- JWT хранится в `Secure` cookie или session; `@login_required` декоратор проверяет токен через middleware.
- При выходе (`/logout`) cookie удаляется.

## 7. Статический фронтенд
Стили копируются из `frontend/drafts/*.css`, подключаются через `static` файловую структуру Django.

## 8. Поток взаимодействия (Mermaid)

```mermaid
flowchart LR
  Frontend[Django Templates] -->|JWT requests| Backend["FastAPI /auth, /devices"]
  Dashboard["GET /dashboard"] --> Devices[FastAPI GET /devices]
  Devices --> Telemetry[FastAPI GET /telemetry/{device_id}]
  Telemetry -->|data| ChartJS[Charts]
  ControlButton -->|PUT /devices/{id}/control| Backend
  NotificationsPage -->|GET/PUT| Backend
  Backend --> ThingsBoard[ThingsBoard API]
  ThingsBoard --> Backend
```

## 9. Следующие шаги
- Реализовать `views.py` и `forms.py` для каждого приложения.
- Настроить маршруты (`urls.py`) чтобы логика `dashboard`, `greenhouse`, `notifications` была читаема.
- Добавить тесты шаблонов и API-клиента.
