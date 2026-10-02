import json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
PATH=Path("data/submission-ledger.json")
def _load(): return json.loads(PATH.read_text()) if PATH.exists() else {}
def key(url): return urlparse(url).netloc.lower().removeprefix("www.")
def seen(url):
    x=_load().get(key(url),{})
    return x.get("status") in {"SUBMITTED","PENDING_APPROVAL","LIVE"}
def record(url,status,details=""):
    PATH.parent.mkdir(exist_ok=True)
    d=_load(); d[key(url)]={"url":url,"status":status,"details":details,"updated_at":datetime.now(timezone.utc).isoformat()}
    PATH.write_text(json.dumps(d,indent=2,sort_keys=True))
