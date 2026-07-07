import time
import json
import random
import paho.mqtt.client as mqtt

# --- НАСТРОЙКИ THINGSBOARD ---
BROKER = "127.0.0.1" 
PORT = 1883  # Используем порт 1883 (его держит ваш контейнер ThingsBoard)

# ⚠️ ВСТАВЬТЕ СЮДА ТОКЕН ВАШЕГО УСТРОЙСТВА ИЗ ИНТЕРФЕЙСА THINGSBOARD
ACCESS_TOKEN = 'vc2TE5YXUTr9qF5Hkkbw'

# Строгие топики ThingsBoard API
TOPIC_TELEMETRY = "v1/devices/me/telemetry"
TOPIC_RPC_REQ = "v1/devices/me/rpc/request/+"

# --- ВНУТРЕННЕЕ СОСТОЯНИЕ ТЕПЛИЦЫ ---
device_state = {
    "temp": 22.5,
    "hum": 45.0,
    "window_state": "close"  # close или open
}

is_connected = False

# --- ОБРАБОТКА RPC КОМАНД ОТ THINGSBOARD ---
def on_message(client, userdata, msg):
    global device_state
    try:
        # Извлекаем ID запроса из топика (ThingsBoard требует ответ обратно)
        request_id = msg.topic.split('/')[-1]
        payload = json.loads(msg.payload.decode())
        
        print(f"\n[ThingsBoard RPC] Получена команда (ID {request_id}): {payload}")
        
        # ThingsBoard шлет команды через "method" и "params"
        method = payload.get("method")
        params = payload.get("params") # Может быть true/false, если это виджет-переключатель
        
        # Обработка разных вариантов вызова (кнопка RPC или виджет Switch)
        if method == "openWindow" or (method == "setWindowState" and params is True) or payload.get("action") == "open":
            print("[Имитация] ThingsBoard скомандовал ОТКРЫТЬ форточку...")
            device_state["window_state"] = "open"
            
        elif method == "closeWindow" or (method == "setWindowState" and params is False) or payload.get("action") == "close":
            print("[Имитация] ThingsBoard скомандовал ЗАКРЫТЬ форточку...")
            device_state["window_state"] = "close"
            
        # Двусторонний RPC в ThingsBoard требует обязательного ответа в топик response
        response_topic = f"v1/devices/me/rpc/response/{request_id}"
        response_payload = {"success": True, "current_state": device_state["window_state"]}
        client.publish(response_topic, json.dumps(response_payload))
        print(f"[ThingsBoard RPC] Ответ отправлен успешно.")
            
    except Exception as e:
        print(f"Ошибка обработки RPC запроса: {e}")

# --- СЛУЖЕБНЫЕ ФУНКЦИИ MQTT ---
def on_connect(client, userdata, flags, rc):
    global is_connected
    if rc == 0:
        print("[ОК] Успешно подключились к ThingsBoard!")
        is_connected = True
        # Подписываемся на RPC команды
        client.subscribe(TOPIC_RPC_REQ)
    elif rc == 5:
        print("[ОШИБКА] ThingsBoard отклонил подключение! Проверьте ACCESS_TOKEN — он указан неверно.")
        is_connected = False
    else:
        print(f"[ОШИБКА] Ошибка подключения. Код: {rc}")
        is_connected = False

def on_disconnect(client, userdata, rc):
    global is_connected
    print(f"[ВНИМАНИЕ] Связь с ThingsBoard разорвана. Код: {rc}")
    is_connected = False

# --- ИНИЦИАЛИЗАЦИЯ КЛИЕНТА ---
try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
except AttributeError:
    client = mqtt.Client()

# Настраиваем авторизацию по Токену Устройства
client.username_pw_set(ACCESS_TOKEN, password=None)

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

print(f"Подключение к ThingsBoard ({BROKER}:{PORT})...")
try:
    client.connect(BROKER, PORT, 60)
except Exception as e:
    print(f"[КРИТИЧЕСКАЯ ОШИБКА] Не удалось достучаться до ThingsBoard: {e}")

client.loop_start()

# --- ЦИКЛ ОТПРАВКИ ДАННЫХ ---
try:
    while True:
        if is_connected:
            # Симулируем небольшое колебание датчиков
            device_state["temp"] += round(random.uniform(-0.1, 0.1), 1)
            device_state["hum"] += round(random.uniform(-0.2, 0.2), 1)

            # Формируем пакет телеметрии
            telemetry_data = {
                "temperature": round(device_state["temp"], 1),
                "humidity": round(device_state["hum"], 1),
                "windowState": device_state["window_state"]
            }
            
            try:
                client.publish(TOPIC_TELEMETRY, json.dumps(telemetry_data))
                print(f"[Телеметрия -> ThingsBoard] Отправлено: {telemetry_data}")
            except Exception as e:
                print(f"Ошибка публикации: {e}")
        else:
            print("[Ожидание] Нет связи с ThingsBoard. Проверьте токен или статус контейнера...")
            
        time.sleep(5)

except KeyboardInterrupt:
    print("\nВыход из симулятора...")
    client.loop_stop()
    client.disconnect()