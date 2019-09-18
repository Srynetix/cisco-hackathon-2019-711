# Smart Spaces Hackathon - Team 7 + 11

Requirements:

- Python 3.6+
- pip

## Quick start

Create a `local_config.py` file in the `hackathon` folder to override configuration variables:

*Example:*
```python
MERAKI_CAMERA_SERIALS = ["Q2GV-FE9K-QSMA"]
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

# 4. Start the server
python start.py
```
