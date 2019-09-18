"""API methods."""

import requests

from . import config
from meraki_sdk.meraki_sdk_client import MerakiSdkClient

def get_camera_analytics(serial):
    return f"https://api.meraki.com/api/v0/devices/{serial}/camera/analytics/live"

def get_camera_snapshot(network, serial):
    url = f"https://api.meraki.com/api/v0/networks/{network}/cameras/{serial}/snapshot"
    return requests.post(url, headers={"X-Cisco-Meraki-API-Key": config.MERAKI_AUTH_TOKEN})

def get_available_room_api(meeting_length):
    url = f"{config.DATA_API_BASE_URL}/room/available?length={meeting_length}"
    return requests.get(url)

def attendants_suggestion_api(person_email):
    url = f"{config.DATA_API_BASE_URL}/person/suggest/{person_email}"
    return requests.post(url)

def identify_person_api(person):
    url= f"{config.DATA_API_BASE_URL}/{person}/identify"
    return requests.get(url)

def get_room_device_info_api(room_title):
    url = f"{config.DATA_API_BASE_URL}/room/{room_title}/device"
    return requests.post(url)


"""
def get_camera_snapshot_sdk(network, serial):
    #Using SDK 
    try:
        client = MerakiSdkClient(config.MERAKI_AUTH_TOKEN)
        return client.cameras.generate_network_camera_snapshot({'network_id':network,
                                                                'serial' : serial})
    except Exception as err:
        print(str(err))
"""
