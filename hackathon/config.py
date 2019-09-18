"""
Configuration variables.

- MERAKI_CAMERA_SERIALS (List[str]):    Camera serials list
- MERAKI_ORGANIZATION_ID (str):         Meraki organization ID
- MERAKI_AUTH_TOKEN (str):              Meraki authentication token
- MQTT_BROKER_URL (str):                MQTT broker URL
- MQTT_BROKER_PORT (int):               MQTT broker port
"""

MERAKI_CAMERA_SERIALS = []
MERAKI_ORGANIZATION_ID = None
MQTT_BROKER_URL = "mqtt.ciscodemos.co"
MQTT_BROKER_PORT = 1883
ROOM_DATA = {}

try:
    from .local_config import *
except ImportError:
    pass
