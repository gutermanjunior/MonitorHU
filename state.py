import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def load_snapshot():
    path = DATA_DIR / "last_snapshot.json"
    if not path.exists():
        return {"especialidades": []}
    return json.loads(path.read_text())


def save_snapshot(especialidades):
    path = DATA_DIR / "last_snapshot.json"
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "especialidades": sorted(especialidades),
    }
    path.write_text(json.dumps(snapshot, indent=2))


def update_heartbeat(status="ok"):
    path = DATA_DIR / "heartbeat.json"
    heartbeat = {
        "last_run": datetime.now().isoformat(),
        "status": status,
    }
    path.write_text(json.dumps(heartbeat, indent=2))
