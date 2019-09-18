"""API methods."""

import requests

def get_camera_analytics(serial):
    return f"https://api.meraki.com/api/v0/devices/{serial}/camera/analytics/live"

def get_camera_snapshot(network, serial):
    url = f"https://api.meraki.com/api/v0/networks/{network}/cameras/{serial}/snapshot"
    return requests.post(url, headers={"X-Cisco-Meraki-API-Key": "27f8ebc0f10a22ad5d6455ced0438f27c9e48147"})
