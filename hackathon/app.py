import asyncio
import json
import logging
import re
import time
from typing import Any, Optional

from flask import Flask, request
from flask_mqtt import Mqtt
import requests
import xows

from . import api, config
from meraki_sdk.meraki_sdk_client import MerakiSdkClient

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app generation
app = Flask(__name__)

# MQTT client configuration
app.config["MQTT_BROKER_URL"] = config.MQTT_BROKER_URL
app.config["MQTT_BROKER_PORT"] = config.MQTT_BROKER_PORT
mqtt = Mqtt(app)

# Creating asyncio loop
loop = asyncio.get_event_loop()

# Regex to extract the camera serial and zone ID
MQTT_ZONE_RGX = re.compile(r"/merakimv/(?P<serial>[0-9A-Z-]+)/(?P<zone_id>[0-9A-Z]+)")
# Current camera state: serial as a key and people count as value
CAMERA_STATE = {}
# Current warn state: username set
WARN_STATE = set({})
# Enter event enabled
ENTER_EVENT_ENABLED = False
# Has the enter event been triggered (only one for the demo)
ENTER_EVENT_TRIGGERED = False
# When was the last warn event
LAST_WARN_EVENT = 0
# Meeting is started
MEETING_STARTED = False
# Warn event enabled
WARN_EVENT_ENABLED = False
# Is the event currently triggering
WARN_EVENT_TRIGGERING = False
# Wait threshold for the warn event
WARN_EVENT_THRESHOLD = 7
# Warn count
WARN_COUNT = 0
# Recording event enabled
RECORDING_EVENT_ENABLED = False
# Recording event trigerred
RECORDING_EVENT_TRIGGERED = False
# Second username (for demo purposes)
SECOND_USERNAME = "John Doe"

###########
# Utilities

def get_camera_room(camera_serial: str) -> Optional[dict]:
    """Get room associated to camera.

    Args:
        camera_serial (str): Camera serial

    Returns:
        Optional[dict]: Room information
    """
    response = api.get_camera_room_api(camera_serial)
    return response.json()


def get_all_devices(organization_id=None, network_id=None) -> list:
    """Get all devices.

    Returns:
        Optional[dict]: Devices list
    """

    passFilter = False if organization_id is not None else True
    avai_devices = []
    client = MerakiSdkClient(config.MERAKI_AUTH_TOKEN)
    orgs = client.organizations.get_organizations()
    avai_orga =  [{'organization_id': orgs[x]} for x in orgs if (not passFilter and orgs[x] == organization_id) or passFilter]
    networks = client.networks.get_organization_networks(avai_orga)
    if networks:
        for network in networks:
            if network_id:
                if network['id'] == network_id:
                    avai_devices.append( client.devices.get_network_devices(network['id']))
            else:
                avai_devices.append( client.devices.get_network_devices(network['id']))

    return avai_devices


def get_camera_network(camera_serial: str) -> dict:
    """Get network associated to camera.

    Args:
        camera_serial (str): Camera serial

    Returns:
        str: Network informations
    """
    client = MerakiSdkClient(config.MERAKI_AUTH_TOKEN)
    try:
        orgs = client.organizations.get_organizations()
        all_organizations = {}

        for org in orgs:
            all_organizations['organization_id'] = org['id']

        if all_organizations:  # make sure it's not an empty collection
            networks = client.networks.get_organization_networks(all_organizations)
            if networks:
                for network in networks:
                    devices = client.devices.get_network_devices(network['id'])
                    for device in devices:
                        if device['serial'] == camera_serial:
                            return network

    except Exception as err:
        logging.error(str(err))

    return {
        "id": "L_634444597505825671"
    }


def get_room_meeting(room_id: str) -> Optional[dict]:
    """Get meeting associated to room.

    Args:
        room_id (str): Room ID

    Returns:
        Optional[dict]: Meeting information
    """
    response = api.get_current_meeting_api(room_id)
    return response.json()


def get_available_room(meeting_length: int) -> Optional[dict]:
    """Get meeting associated to room.

    Args:
        room_id (str): Room ID

    Returns:
        Optional[dict]: Meeting information
    """
    try:
        return api.get_available_room_api(meeting_length)
    except Exception as err:
        logger.error(str(err))



def get_room_t10(room_id: str) -> Optional[dict]:
    """Get T10 associated to room.

    Args:
        room_id (str): Room ID

    Returns:
        Optional[dict]: T10 information
    """
    response = api.get_room_device_info_api(room_id)
    return response.json()


def take_picture_from_camera(network_id: str, camera_serial: str) -> dict:
    """Take picture from camera.

    Args:
        network_id (str): Network ID
        camera_serial (str): Camera serial

    Returns:
        dict: Picture data
    """
    data = api.get_camera_snapshot(network_id, camera_serial)
    if data.status_code != 202:
        # Fake data
        return {
            "url": "https://spn4.meraki.com/stream/jpeg/snapshot/b2d123asdf423qd22d2",
            "expiry": "Access to the image will expire one day"
        }

    return data.content


def identify_user(picture: str) -> Optional[dict]:
    """Identify user using picture.

    Args:
        picture (str): Picture data

    Returns:
        Optional[dict]: User information
    """
    data = api.identify_person_api(picture)
    return data.json()


async def async_send_raw_message_to_t10(ip: str, username: str, password: str, message: str) -> dict:
    """Send raw message to T10.

    Args:
        ip (str): Device IP
        username (str): Username
        password (str): Password
        message (str): Message

    Returns:
        dict: Response
    """
    async with xows.XoWSClient(ip, username, password) as client:
        encoded_message = f"711:{message}"
        logger.info(f"Sending message {encoded_message} to T10 {ip} ...")
        return await client.xCommand(['Message', 'Send'], Text=encoded_message)


def send_raw_message_to_t10(ip: str, username: str, password: str, message: str) -> dict:
    """Send raw message to T10.

    Args:
        ip (str): Device IP
        username (str): Username
        password (str): Password
        message (str): Message

    Returns:
        dict: Response
    """
    return loop.run_until_complete(async_send_raw_message_to_t10(ip, username, password, message))


def get_person_meeting_from_camera(camera_serial: str) -> Optional[dict]:
    """Get person and meeting from camera serial.

    Args:
        camera_serial (str): Camera serial

    Returns:
        Optional[dict]: Data
    """
    # Get the network
    network_data = get_camera_network(camera_serial)
    # Get the camera capture
    capture_data = take_picture_from_camera(network_data["id"], camera_serial)
    # Identify person
    person_data = identify_user(capture_data["url"])
    # Get the room ID associated to the camera
    room_data = get_camera_room(camera_serial)
    # Get the T10 device associated to the room
    t10_data = get_room_t10(room_data["room"])
    # Get the meeting
    meeting = get_room_meeting(room_data["room"])

    if meeting:
        return {
            't10_data': t10_data,
            'username': person_data["identified_person"]
        }


def send_json_message_to_t10(ip: str, username: str, password: str, message: dict) -> dict:
    """Send JSON message to T10.

    Args:
        message (dict): Message to send

    Returns:
        dict: Response
    """
    json_data = json.dumps(message)
    return loop.run_until_complete(async_send_raw_message_to_t10(ip, username, password, json_data))


def send_json_message_to_bot(message: dict):
    """Send JSON message to bot.

    Args:
        message (dict): Message
    """
    requests.post(config.BOT_URL, json=message)


def handle_t10_message(message: dict):
    """Handle T10 message.

    Args:
        message (dict): Message
    """
    global MEETING_STARTED, LAST_WARN_EVENT

    message_id = message.get("messageId")
    room_id = message.get("roomId")
    choice = message.get("choice")

    if message_id == 1 and choice == "yes":
        # Get meeting info
        meeting = get_room_meeting(room_id)

        if not MEETING_STARTED:
            LAST_WARN_EVENT = time.time()
            MEETING_STARTED = True

        send_json_message_to_bot({
            "roomId": room_id,
            "attendants": meeting["attendants"]
        })

    elif message_id == 4 and choice == "yes":
        pass


def get_zone_name(camera_serial: str, zone_id: str) -> str:
    """Get zone name.

    Args:
        camera_serial (str): Camera serial
        zone_id (str): Zone ID

    Returns:
        str: Zone name
    """
    camera = next(x for x in config.MERAKI_CAMERAS if x["serial"] == camera_serial)
    zone = next(x for x in camera.get("zones", []) if x["id"] == zone_id)
    return zone["name"]


def handle_meraki_zone(camera_serial: str, zone_id: str, camera_data: dict):
    """Handle Meraki MQTT data.

    Args:
        camera_serial (str): Camera serial
        zone_id (str): Zone ID
        camera_data (dict): Camera data
    """
    global CAMERA_STATE
    zone_name = get_zone_name(camera_serial, zone_id)

    state_key = f"{camera_serial}-{zone_id}"
    previous_persons_count = CAMERA_STATE.get(state_key, 0)
    current_persons_count = camera_data["counts"]["person"]

    if zone_name == "Far" and current_persons_count > 0:
        logger.debug(f"[DEBUG] Someone is too far in the room (camera: {camera_serial})")
        start_too_far_scenario(camera_serial)

    elif zone_name == "Start" and current_persons_count > previous_persons_count:
        logger.debug(f"[DEBUG] Someone entered the room (camera: {camera_serial})")
        start_entered_scenario(camera_serial)

    CAMERA_STATE[state_key] = current_persons_count


def start_entered_scenario(camera_serial: str):
    """Start the room enter scenario.

    Args:
        camera_serial (str): Camera serial
    """
    global ENTER_EVENT_TRIGGERED, RECORDING_EVENT_TRIGGERED

    if ENTER_EVENT_ENABLED:
        if ENTER_EVENT_TRIGGERED:
            return

        # Set the trigger
        ENTER_EVENT_TRIGGERED = True

        related_meeting_data = get_person_meeting_from_camera(camera_serial)

        if related_meeting_data:
            send_json_message_to_t10(
                related_meeting_data['t10_data']["credentials"]["IP"],
                related_meeting_data['t10_data']["credentials"]["username"],
                related_meeting_data['t10_data']["credentials"]["password"],
                {
                    "messageId": 1,
                    'username': related_meeting_data['username']
                }
            )

    if RECORDING_EVENT_ENABLED:
        if RECORDING_EVENT_TRIGGERED:
            return

        # Set the trigger
        RECORDING_EVENT_TRIGGERED = True

        related_meeting_data = get_person_meeting_from_camera(camera_serial)

        if related_meeting_data:
            send_json_message_to_t10(
                related_meeting_data['t10_data']["credentials"]["IP"],
                related_meeting_data['t10_data']["credentials"]["username"],
                related_meeting_data['t10_data']["credentials"]["password"],
                {
                    "messageId": 4,
                    'username': related_meeting_data['username']
                }
            )


def start_too_far_scenario(camera_serial: str):
    """Start the "too far" scenario.

    Args:
        camera_serial (str): Camera serial
    """
    global WARN_EVENT_TRIGGERING, LAST_WARN_EVENT, WARN_COUNT

    # Check if we are not triggering
    if WARN_EVENT_TRIGGERING or not WARN_EVENT_ENABLED or not MEETING_STARTED:
        return

    # Check for elapsed time
    now = time.time()
    if now - LAST_WARN_EVENT < WARN_EVENT_THRESHOLD:
        return

    # Check for warn count
    if WARN_COUNT >= 2:
        return

    WARN_EVENT_TRIGGERING = True

    related_meeting_data = get_person_meeting_from_camera(camera_serial)
    username = related_meeting_data['username']

    # Already triggered
    if username in WARN_STATE:
        username = SECOND_USERNAME

    WARN_COUNT += 1

    # Mark the username as warned
    WARN_STATE.add(username)

    if related_meeting_data:
        send_json_message_to_t10(
            related_meeting_data['t10_data']["credentials"]["IP"],
            related_meeting_data['t10_data']["credentials"]["username"],
            related_meeting_data['t10_data']["credentials"]["password"],
            {
                "messageId": 3,
                "username": username,
                "first": len(WARN_STATE) == 1
            }
        )

    # Warn
    LAST_WARN_EVENT = time.time()
    WARN_EVENT_TRIGGERING = False


def handle_bot_message(message: dict):
    """Handle bot message.

    Args:
        message (dict): Message
    """
    message_id = message.get("messageId", 0)
    room_id = message.get("roomId", None)

    if message_id == 2:
        # Send a late choice to the T10
        t10_data = get_room_t10(room_id)
        send_json_message_to_t10(
            t10_data["credentials"]["IP"],
            t10_data["credentials"]["username"],
            t10_data["credentials"]["password"],
            {
                "messageId": message_id,
                "username": message.get("Name", None),
                "responseChoice": int(message.get("time", "0"))
            }
        )


#############
# MQTT routes

@mqtt.on_connect()
def handle_mqtt_connect(client, userdata, flags, rc):
    """Handle MQTT connections.

    Args:
        client (Client): MQTT client
        userdata (Any): User data
        flags (Any): Flags
        rc (Any): RC
    """
    for camera in config.MERAKI_CAMERAS:
        serial = camera["serial"]
        zones = camera.get("zones", [])
        for zone in zones:
            zone_id = zone["id"]
            mqtt.subscribe(f'/merakimv/{serial}/{zone_id}')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    """Handle a MQTT incoming message.

    Args:
        client (Client): MQTT client
        userdata (Any): User data
        message (Message): Message object
    """
    match = MQTT_ZONE_RGX.search(message.topic)
    if match:
        handle_meraki_zone(match.group("serial"), match.group("zone_id"), json.loads(message.payload.decode()))

#############
# HTTP routes

@app.route('/on-t10-message', methods=["POST"])
def on_t10_message():
    """Wait for T10 incoming message.

    Returns:
        str: Route output
    """
    handle_t10_message(request.get_json())
    return "ok"


@app.route('/on-bot-message', methods=["POST"])
def on_bot_message():
    """Wait for bot incoming message.

    Returns:
        str: Route output
    """
    handle_bot_message(request.get_json())
    return "ok"


@app.route('/enable-enter-events', methods=["POST"])
def enable_enter_events():
    """Enable enter events.

    Returns:
        str: Route output
    """
    global ENTER_EVENT_ENABLED
    ENTER_EVENT_ENABLED = True

    print("ENTER EVENT ENABLED")

    return "ok"


@app.route('/enable-warn-events', methods=["POST"])
def enable_warn_events():
    """Enable warn events.

    Returns:
        str: Route output
    """
    global WARN_EVENT_ENABLED
    WARN_EVENT_ENABLED = True

    print("WARN EVENT ENABLED")

    return "ok"


@app.route('/enable-recording-events', methods=["POST"])
def enable_recording_events():
    """Enable recording events.

    Returns:
        str: Route output
    """
    global RECORDING_EVENT_ENABLED
    RECORDING_EVENT_ENABLED = True

    print("RECORDING EVENT ENABLED")

    return "ok"


#############
# Test routes

@app.route('/test-t10-message', methods=["POST"])
def test_t10_message():
    """Test message send to the T10 using a hardcoded device.

    Returns:
        str: Route output
    """
    send_json_message_to_t10("10.89.130.68", "cisco", "cisco", request.get_json())
    return "ok"


@app.route('/test-2nd-scenario', methods=["GET"])
def test_2nd_scenario():
    """Test the room enter scenario.

    Returns:
        str: Route output
    """
    start_entered_scenario(config.MERAKI_CAMERAS[0]["serial"])
    return "ok"


@app.route('/test-too-far-scenario', methods=["GET"])
def test_too_far_scenario():
    """Test the "too far" scenario.

    Returns:
        str: Route output
    """
    start_too_far_scenario(config.MERAKI_CAMERAS[0]["serial"])
    time.sleep(WARN_EVENT_THRESHOLD)
    start_too_far_scenario(config.MERAKI_CAMERAS[0]["serial"])
    return "ok"


@app.route('/test-bot-message', methods=["POST"])
def test_bot_message():
    """Test the bot message.

    Returns:
        str: Route output
    """
    send_json_message_to_bot(request.get_json())
    return "ok"
