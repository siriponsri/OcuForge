import os
from pathlib import Path
import sys
from urllib.parse import quote

password = Path("/run/secrets/mongo_app_password").read_text().strip()
if len(password) < 24:
    raise SystemExit("Missing strong local database secret")
os.environ["MONGO_URI"] = (
    "mongodb://ocuforge_app:" + quote(password, safe="") + "@mongo:27017/ocuforge?authSource=ocuforge"
)
os.umask(0o077)
os.execvp(sys.argv[1], sys.argv[1:])
