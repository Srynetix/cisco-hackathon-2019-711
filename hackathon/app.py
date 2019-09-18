import asyncio
import json
import re

from flask import Flask, request
from flask_mqtt import Mqtt
import requests
import xows

from . import config

app = Flask(__name__)
app.config["MQTT_BROKER_URL"] = config.MQTT_BROKER_URL
app.config["MQTT_BROKER_PORT"] = config.MQTT_BROKER_PORT
mqtt = Mqtt(app)

loop = asyncio.get_event_loop()

MQTT_TOPIC_RGX = re.compile(r"/merakimv/(?P<serial>[0-9A-Z-]+)/raw_detections")
CAMERA_STATE = {}

###########
# Utilities

async def fetch_info():
    async with xows.XoWSClient('10.89.130.68', 'cisco', 'cisco') as client:
        data = await client.xCommand(['Message', 'Send'], Text='Hello from Python')
        print(data)
        # await client.wait_until_closed()

#############
# MQTT routes

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    for serial in config.MERAKI_CAMERA_SERIALS:
        mqtt.subscribe(f'/merakimv/{serial}/raw_detections')

@mqtt.on_message()
def handle_message(client, userdata, message):
    global CAMERA_STATE

    match = MQTT_TOPIC_RGX.search(message.topic)
    if match:
        camera_serial = match.group("serial")
        camera_data = json.loads(message.payload.decode())
        objects = camera_data["objects"]
        persons = [o for o in objects if o["type"] == "person"]
        current_persons_count = len(persons)
        previous_persons_count = CAMERA_STATE.get(camera_serial, 0)

        # if current_persons_count != previous_persons_count:
            # print(f"There are now {current_persons_count} people on camera {camera_serial}")

        # Update people count
        CAMERA_STATE[camera_serial] = current_persons_count

#############
# HTTP routes

@app.route('/json', methods=['POST'])
def json_test():
    print(request.get_json())
    return "ok"

@app.route('/xows-test')
def xows_test():
    data = loop.run_until_complete(fetch_info())
    return "ok"
