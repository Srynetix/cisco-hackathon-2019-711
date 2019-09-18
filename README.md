# Smart Spaces Hackathon - Team 7 + 11

Requirements:

- Python 3.7+
- pip

## Configuration required

- Enable Websocket on the T10

## Quick start

Create a `local_config.py` file in the `hackathon` folder to override configuration variables:

*Example:*
```python
MERAKI_CAMERAS = [
    {
        "serial": "Q2GV-SXBN-ACWY",
        "zones": [
            {
                "id": "634444597505818687",
                "name": "Too far away"
            },
            {
                "id": "634444597505818688",
                "name": "Just arrived"
            }
        ]
    }
]
```

Then you can start the procedure:

```bash
# 1. Install the virtualenv package
pip install virtualenv

# 2. Create the virtualenv
virtualenv -p python3 ./venv

# 3. Source the virtualenv
# - For Windows
. ./venv/Scripts/activate
# - For UNIX-like
. ./venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start the server
python start.py
```
