"""API methods."""

def get_camera_analytics(serial):
    return f"https://api.meraki.com/api/v0/devices/{serial}/camera/analytics/live"
