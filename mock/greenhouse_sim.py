import time
import json
import random
import paho.mqtt.client as mqtt

# --- НАСТРОЙКИ ---
BROKER = "127.0.0.1" 
PORT = 1883
TOPIC_TELEMETRY = "greenhouse/sensor_1/telemetry"
TOPIC_RPC_REQ = "greenhouse/actuator_1/rpc/request"

# --- ВНУТРЕННЕЕ СОСТОЯНИЕ ТЕПЛИЦЫ ---
device_state = {
    "temp": 22.5,
    "hum": 45.0,
    "window_state": "close"  # Может быть: close, opening, open, closing
}

is_connected = False

# --- ОБРАБОТКА ВХОДЯЩИХ RPC КОМАНД ---
def on_message(client, userdata, msg):
    global device_state
    try:
        # Декодируем пришедший JSON-пакет
        payload = json.loads(msg.payload.decode())
        print(f"\n[RPC] Получена команда извне: {payload}")
        
        action = payload.get("action")
        
        if action == "open":
            print("[Имитация] Начинаем открывать форточку...")
            device_state["window_state"] = "opening"
            device_state["window_state"] = "open"
            print("[Имитация] Форточка успешно ОТКРЫТА!")
            
        elif action == "close":
            print("[Имитация] Начинаем закрывать форточку...")
            device_state["window_state"] = "closing"
            device_state["window_state"] = "close"
            print("[Имитация] Форточка успешно ЗАКРЫТА!")
            
    except Exception as e:
        print(f"Ошибка обработки RPC запроса: {e}")

# --- СЛУЖЕБНЫЕ ФУНКЦИИ MQTT ---
def on_connect(client, userdata, flags, rc):
    global is_connected
    if rc == 0:
        print("[ОК] Успешно подключились к Mosquitto!")
        is_connected = True
        # ОБЯЗАТЕЛЬНО подписываемся на топик команд при подключении
        client.subscribe(TOPIC_RPC_REQ)
    else:
        print(f"[ОШИБКА] Брокер отклонил подключение. Код: {rc}")
        is_connected = False

def on_disconnect(client, userdata, rc):
    global is_connected
    print(f"[ВНИМАНИЕ] Соединение разорвано. Код: {rc}")
    is_connected = False

# --- ИНИЦИАЛИЗАЦИЯ КЛИЕНТА ---
try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
except AttributeError:
    client = mqtt.Client()

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message  # Привязываем обработчик сообщений

print("Попытка установить связь с брокером...")
try:
    client.connect(BROKER, PORT, 60)
except Exception as e:
    print(f"[КРИТИЧЕСКАЯ ОШИБКА] Не удалось достучаться до брокера: {e}")

# Запускаем фоновый поток, который слушает сервер и обрабатывает on_message
client.loop_start()

# --- ОСНОВНОЙ ЦИКЛ ОТПРАВКИ ТЕЛЕМЕТРИИ ---
try:
    while True:
        if is_connected:
            # Слегка изменяем датчики для реалистичности
            device_state["temp"] += round(random.uniform(-0.1, 0.1), 1)
            device_state["hum"] += round(random.uniform(-0.2, 0.2), 1)

            # Формируем пакет телеметрии на основе ТЕКУЩЕГО состояния
            telemetry_data = {
                "temp": round(device_state["temp"], 1),
                "hum": round(device_state["hum"], 1),
                "window_state": device_state["window_state"] # Передает актуальное состояние!
            }
            
            try:
                client.publish(TOPIC_TELEMETRY, json.dumps(telemetry_data))
                print(f"[Телеметрия] Отправлено: {telemetry_data}")
            except Exception as e:
                print(f"Ошибка при публикации: {e}")
        else:
            print("[Ожидание] Нет связи с брокером Mosquitto...")
            
        time.sleep(8)

except KeyboardInterrupt:
    print("\nВыход из симулятора...")
    client.loop_stop()
    client.disconnect()