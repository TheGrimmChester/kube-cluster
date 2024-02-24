#!/usr/bin/python3 -u

from bluepy.btle import Peripheral, UUID, DefaultDelegate
from paho.mqtt import client as mqtt_client
from datetime import date
import time
import logging
import sys
import os
import random

FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

broker = os.environ.get("MQTT_HOST", None)
port = os.environ.get("MQTT_PORT", 1883)
mqtt_username = os.environ.get("MQTT_USERNAME", None)
mqtt_password = os.environ.get("MQTT_PASSWORD", None)
client_id = f'quality_air-{random.randint(0, 1000)}'

# Replace with the MAC address of your RCXAZAIR device
device_address = os.environ.get("MAC_ADDRESS", None)

characteristic_uuid = os.environ.get("UUID", None)

def on_disconnect(client, userdata, rc):
    logging.info("Disconnected with result code: %s", rc)
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        logging.info("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            logging.info("Reconnected successfully!")
            return
        except Exception as err:
            logging.error("%s. Reconnect failed. Retrying...", err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)
    sys.exit(1)

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, "air_quality")
    client.username_pw_set(mqtt_username, mqtt_password)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(broker, port)
    return client

class RcxazairHandler:
    client = connect_mqtt()

    def __init__(self):
        # Initialisation de vos capteurs ou autres éléments nécessaires
        pass

    def handle_message(self, msg):
        if len(msg) < 4:
            return

        def u16(offset):
            return (msg[offset] << 8) + msg[offset + 1]

        type_value = (msg[0] << 24) + (msg[1] << 16) + (msg[2] << 8) + msg[3]

        if type_value == 0x23061004:
            if len(msg) < 8:
                return
            temp = u16(4) * 0.1
            rel_hum = u16(6)
            self.handle_temp_and_humidity(temp, rel_hum)
        elif type_value == 0x23081004:
            if len(msg) < 10:
                return
            co2_ppm = u16(4)
            tvoc = u16(6)
            hcho = u16(8)
            self.handle_co2_tvoc_hcho(co2_ppm, tvoc, hcho)
        elif type_value == 0x23081007:
            if len(msg) < 10:
                return
            pmc_1_0_ugm3 = u16(4)
            pmc_2_5_ugm3 = u16(6)
            pmc_10_0_ugm3 = u16(8)
            self.handle_pmc_values(pmc_1_0_ugm3, pmc_2_5_ugm3, pmc_10_0_ugm3)
        else:
            print(f"Got unknown message type {type_value}")

    def handle_temp_and_humidity(self, temp, rel_hum):
        # Logique pour gérer la température et l'humidité
        self.client.publish("air_quality_temperature", temp)
        self.client.publish("air_quality_relative_humidity", rel_hum)
        print(f"Temperature: {temp}°C, Relative Humidity: {rel_hum}%")

    def handle_co2_tvoc_hcho(self, co2_ppm, tvoc, hcho):
        # Logique pour gérer les valeurs CO2, TVOC, HCHO
        self.client.publish("air_quality_co2", co2_ppm)
        self.client.publish("air_quality_tvoc", tvoc / 1000)
        self.client.publish("air_quality_hcho", hcho / 1000)
        print(f"CO2: {co2_ppm} ppm, TVOC: {tvoc}, HCHO: {hcho}")

    def handle_pmc_values(self, pmc_1_0_ugm3, pmc_2_5_ugm3, pmc_10_0_ugm3):
        # Logique pour gérer les valeurs PM1.0, PM2.5, PM10.0
        self.client.publish("air_quality_pm1_0", pmc_1_0_ugm3)
        self.client.publish("air_quality_pm2_5", pmc_2_5_ugm3)
        self.client.publish("air_quality_pm10", pmc_10_0_ugm3)
        print(f"PM1.0: {pmc_1_0_ugm3} µg/m³, PM2.5: {pmc_2_5_ugm3} µg/m³, PM10.0: {pmc_10_0_ugm3} µg/m³")

class MyDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        rcxazair_handler = RcxazairHandler()
        rcxazair_handler.handle_message(data)

def connect_with_retry(device_address):
    max_retries = 3
    retry_delay = 5  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            peripheral = Peripheral(device_address)
            peripheral.setDelegate(MyDelegate())

            # Your code to enable notifications goes here

            print("Connected successfully!")
            return peripheral

        except Exception as e:
            print(f"Connection attempt {attempt} failed: {e}")
            time.sleep(retry_delay)

    print("Failed to connect after multiple attempts.")
    return None

def reconnect(peripheral, device_address):
    # Disconnect the existing peripheral
    peripheral.disconnect()

    # Attempt to reconnect
    try:
        new_peripheral = Peripheral(device_address)
        new_peripheral.setDelegate(MyDelegate())
        # Your code to enable notifications or perform other operations
        return new_peripheral
    except Exception as e:
        print(f"Reconnection failed: {e}")
        return None

def enable_notifications(peripheral, characteristic_handle):
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            # Your code to enable notifications
            peripheral.writeCharacteristic(characteristic_handle + 1, b"\x01\x00", withResponse=True)
            print("Notifications enabled successfully!")
            return True
        except Exception as e:
            print(f"Notification enable attempt {attempt} failed: {e}")
            # Retry after a delay
            time.sleep(5)

    print("Failed to enable notifications after multiple attempts.")
    return False

polling_interval = 10  # 10 seconds

# Example usage
connected_peripheral = connect_with_retry(device_address)

while connected_peripheral:
    try:
        # Rechercher la caractéristique par UUID
        characteristic = connected_peripheral.getCharacteristics(uuid=UUID(characteristic_uuid))[0]

        # Lire la valeur de la caractéristique
        value = characteristic.read()

        # Afficher la valeur lue
        # print(f"Valeur de la caractéristique: {value}")

        connected_peripheral.writeCharacteristic(characteristic.getHandle() + 1, b"\x01\x00", withResponse=True)
    except Exception as e:
        print(f"Error during main code execution: {e}")
        connected_peripheral = reconnect(connected_peripheral, device_address)
        if connected_peripheral is None:
            print("Exiting program due to reconnection failure.")
            break

# Close the BLE connection if it's still open
if connected_peripheral:
    connected_peripheral.disconnect()

