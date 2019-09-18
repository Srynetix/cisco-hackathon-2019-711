"""
Configuration variables.

- MERAKI_CAMERAS (List[dict]):          Camera serials list
- MERAKI_ORGANIZATION_ID (str):         Meraki organization ID
- MERAKI_AUTH_TOKEN (str):              Meraki authentication token
- BOT_URL (str):                        Bot URL
- MQTT_BROKER_URL (str):                MQTT broker URL
- MQTT_BROKER_PORT (int):               MQTT broker port
"""

MERAKI_CAMERAS = []
MERAKI_ORGANIZATION_ID = None
BOT_URL = ""
MQTT_BROKER_URL = "mqtt.ciscodemos.co"
MQTT_BROKER_PORT = 1883
ROOM_DATA = {}
DATA_API_BASE_URL = ""
try:
    from .local_config import *
except ImportError:
    pass
