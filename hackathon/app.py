import asyncio
import json
import logging
import re

from flask import Flask, request
from flask_mqtt import Mqtt
import requests
import xows

from . import config
from .api import get_camera_snapshot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        data = await client.xCommand(['Message', 'Send'], Text="Speak:Hello")

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

        if current_persons_count != previous_persons_count:
            logger.debug(f"[DEBUG] There are now {current_persons_count} people on camera {camera_serial} (previously {previous_persons_count})")

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

@app.route('/snapshot')
def snapshot():
    data = get_camera_snapshot(config.MERAKI_NETWORK_ID, config.MERAKI_CAMERA_SERIALS[0])
    if data.status_code != 202:
        # Fake data
        return {
            "url": "https://spn4.meraki.com/stream/jpeg/snapshot/b2d123asdf423qd22d2",
            "expiry": "Access to the image will expire one day"
        }

    return data.content
