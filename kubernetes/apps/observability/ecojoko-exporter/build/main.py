#!/usr/bin/python3 -u

import json
import time
import re
import requests
import sys
import logging
import os
import random
from datetime import date

from prometheus_client import start_http_server, Gauge, Enum
from prometheus_client import Counter
from paho.mqtt import client as mqtt_client

username = os.environ.get("ECOJOKO_USERNAME")
password = os.environ.get("ECOJOKO_PASSWORD")
gateway = os.environ.get("ECOJOKO_GATEWAY")
device = os.environ.get("ECOJOKO_DEVICE")
broker = os.environ.get("MQTT_HOST", None)
port = os.environ.get("MQTT_PORT", 1883)
mqtt_username = os.environ.get("MQTT_USERNAME", None)
mqtt_password = os.environ.get("MQTT_PASSWORD", None)
ecojoko_consumption_topic = "ecojoko/consumption"
ecojoko_injection_topic = "ecojoko/injection"
ecojoko_instant_topic = "ecojoko/instant"
ecojoko_daily_injection_topic = "ecojoko/daily_injection"
client_id = f'ecojoko-{random.randint(0, 1000)}'

FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

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
    client = mqtt_client.Client(client_id)
    client.username_pw_set(mqtt_username, mqtt_password)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(broker, port)
    return client

def login_and_save_cookie(email, password):
    login_url = 'https://service.ecojoko.com/login'  # Remplacez par l'URL de la page de connexion
    payload = {
        "l": email,
        "p": password
    }

    # Créer une session pour conserver le cookie
    session = requests.Session()

    # Effectuer la requête POST pour soumettre le formulaire de connexion
    response = session.post(login_url, data=json.dumps(payload))

    if response.status_code == 200:
        # Cookie sauvegardé dans la variable 'cookie'
        cookie = session.cookies.get_dict()
        print("Connexion réussie ! Cookie sauvegardé dans la variable 'cookie'.")
        return cookie
    else:
        print("La connexion a échoué. Vérifiez vos identifiants.")
        print(response.status_code)
        sys.exit(1)


ecojoko_daily_injection_gauge = Gauge('ecojoko_daily_injection', 'Ecojoko Daily Injection')
ecojoko_injection_gauge = Gauge('ecojoko_injection', 'Ecojoko Injection')
ecojoko_consumption_gauge = Gauge('ecojoko_consumption', 'Ecojoko Consumption')
ecojoko_instant_gauge = Gauge('ecojoko_instant', 'Ecojoko Instant')
error_count = Counter('ecojoko_injection_failures', 'Failures')

cookies = login_and_save_cookie(username, password)

headers = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Sec-GPC': '1',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://service.ecojoko.com/?conso',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-FR;q=0.8,en-US;q=0.7,en;q=0.6',
}

if __name__ == '__main__':
    server_port = 3226

    print("Running on...")
    print("Port: " + str(server_port) + "\n")

    if broker is not None:
        client = connect_mqtt()

    start_http_server(server_port)
    while True:
        try:
            realtimeConsoResponse = requests.get('https://service.ecojoko.com/gateway/' + gateway + '/device/' + device + '/realtime_conso', headers=headers, cookies=cookies).content.decode('UTF-8')
            print("Realtime conso " + realtimeConsoResponse)
            realtimeConsoResponse = json.loads(realtimeConsoResponse)
            ecojoko_injection = realtimeConsoResponse['real_time']['value']
            ecojoko_consumption = realtimeConsoResponse['real_time']['value']

            if ecojoko_injection > 0:
                ecojoko_injection = 0

            if ecojoko_consumption < 0:
                ecojoko_consumption = 0

            ecojoko_instant_gauge.set(realtimeConsoResponse['real_time']['value'])
            ecojoko_consumption_gauge.set(ecojoko_consumption)
            ecojoko_injection_gauge.set(-ecojoko_injection)

            print("Fetching data for date " + date.today().strftime('%Y-%m-%d'))
            powerstatResponse = requests.get('https://service.ecojoko.com/gateway/' + gateway + '/device/' + device + '/powerstat/d4/' + date.today().strftime('%Y-%m-%d'), headers=headers, cookies=cookies).content.decode('UTF-8')
            print(powerstatResponse)
            powerstatResponse = json.loads(powerstatResponse)
            ecojoko_daily_injection_gauge.set(-powerstatResponse['stat']['period']['kwh_prod'])

            if broker is not None:
                client.publish(ecojoko_injection_topic, -ecojoko_injection)
                client.publish(ecojoko_consumption_topic, ecojoko_consumption)
                client.publish(ecojoko_instant_topic, realtimeConsoResponse['real_time']['value'])
                client.publish(ecojoko_daily_injection_topic, -powerstatResponse['stat']['period']['kwh_prod'])

            time.sleep(5)
        except Exception as e:
            print(e)
            sys.exit(1)
