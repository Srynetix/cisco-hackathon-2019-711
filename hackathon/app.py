import json
import re

from flask import Flask, request
from flask_mqtt import Mqtt
import requests

from . import config

app = Flask(__name__)
app.config["MQTT_BROKER_URL"] = config.MQTT_BROKER_URL
app.config["MQTT_BROKER_PORT"] = config.MQTT_BROKER_PORT
mqtt = Mqtt(app)

MQTT_TOPIC_RGX = re.compile(r"/merakimv/(?P<serial>[0-9A-Z-]+)/raw_detections")
CAMERA_STATE = {}

#############
# MQTT routes

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    for serial in config.CAMERA_SERIALS:
        mqtt.subscribe(f'/merakimv/{serial}/raw_detections')

@mqtt.on_message()
def handle_message(client, userdata, message):
    global CAMERA_STATE

    match = MQTT_TOPIC_RGX.search(message.topic)
    if match:
        camera_serial = match.group("serial")
        print(f"> Camera: {camera_serial}")

        camera_data = json.loads(message.payload.decode())
        objects = camera_data["objects"]
        persons = [o for o in objects if o["type"] == "person"]
        if len(persons) > 0:
            print("PERSONS DETECTED, CALLING BLABLABLA")

        # Update people count
        CAMERA_STATE[camera_serial] = len(persons)

#############
# HTTP routes

@app.route('/json', methods=['POST'])
def json_test():
    print(request.get_json())
    return "ok"
