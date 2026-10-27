# -*- coding: utf-8 -*-
"""
Simulador del sensor de la heladera (reemplaza a un ESP32 real).
- Cada 5 segundos envía temperatura y humedad por MQTT al tópico "heladera/sensor".
- A veces simula que alguien deja la puerta abierta (la temperatura sube).
- Escucha el tópico "heladera/comando": si recibe "ENFRIAR", enciende el
  compresor y la temperatura vuelve a 4 °C.

Requisito: pip install paho-mqtt
Uso:       python simulador_heladera.py
"""

import json
import random
import time

import paho.mqtt.client as mqtt

# --- Configuración ---
BROKER = "localhost"          # El broker MQTT corre dentro de Node-RED
PUERTO = 1883
TOPICO_SENSOR = "heladera/sensor"
TOPICO_COMANDO = "heladera/comando"
INTERVALO_SEGUNDOS = 5

# --- Estado inicial de la heladera ---
temperatura = 4.0   # °C (lo ideal es entre 2 y 8 °C)
humedad = 60.0      # %


def al_conectar(cliente, userdata, flags, reason_code, properties):
    print("[OK] Conectado al broker MQTT")
    cliente.subscribe(TOPICO_COMANDO)
    print(f"[OK] Escuchando órdenes en '{TOPICO_COMANDO}'")


def al_recibir_orden(cliente, userdata, mensaje):
    global temperatura
    orden = mensaje.payload.decode()
    print(f"[ORDEN] Recibí: {orden}")
    if orden == "ENFRIAR":
        temperatura = 4.0
        print("[COMPRESOR] Encendido: la temperatura vuelve a 4 °C")


cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="sensor-heladera")
cliente.on_connect = al_conectar
cliente.on_message = al_recibir_orden

print(f"Conectando a {BROKER}:{PUERTO} ...")
cliente.connect(BROKER, PUERTO)
cliente.loop_start()   # Atiende los mensajes MQTT en segundo plano

try:
    while True:
        # 1 de cada 8 veces, alguien deja la puerta abierta
        if random.random() < 0.125:
            temperatura += random.uniform(5, 7)
            print("[PUERTA] ¡Dejaron la puerta abierta! La temperatura sube.")
        else:
            temperatura += random.uniform(-0.3, 0.3)

        humedad += random.uniform(-1, 1)
        humedad = max(40, min(humedad, 80))

        datos = {
            "temperatura": round(temperatura, 1),
            "humedad": round(humedad, 1),
        }
        cliente.publish(TOPICO_SENSOR, json.dumps(datos))
        print(f"[ENVIADO] {datos}")

        time.sleep(INTERVALO_SEGUNDOS)

except KeyboardInterrupt:
    print("\nSimulador detenido.")
    cliente.loop_stop()
    cliente.disconnect()
