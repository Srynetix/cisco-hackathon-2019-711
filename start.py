"""Starting script."""

import os
import subprocess
import sys

os.environ["FLASK_APP"] = "hackathon.app"

subprocess.call(
    [sys.executable, "-m", "flask", "run", "-h", "0.0.0.0"],
    stderr=sys.stderr, stdout=sys.stdout
)
