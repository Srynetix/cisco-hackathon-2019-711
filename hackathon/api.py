"""API methods."""

import requests

from . import config
from meraki_sdk.meraki_sdk_client import MerakiSdkClient

def get_camera_analytics(serial):
    return f"https://api.meraki.com/api/v0/devices/{serial}/camera/analytics/live"

def get_camera_snapshot(network, serial):
    url = f"https://api.meraki.com/api/v0/networks/{network}/cameras/{serial}/snapshot"
    return requests.post(url, headers={"X-Cisco-Meraki-API-Key": config.MERAKI_AUTH_TOKEN})

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
