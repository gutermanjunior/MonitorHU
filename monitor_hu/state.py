import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def load_snapshot():
    path = DATA_DIR / "last_snapshot.json"
    
    if not path.exists():
        return {"especialidades": [], "is_first_run": True}
    
    try:
        content = path.read_text(encoding='utf-8').strip()
        if not content:
            return {"especialidades": [], "is_first_run": True}
            
        data = json.loads(content)
        data["is_first_run"] = False
        return data
        
    except (json.JSONDecodeError, OSError):
        return {"especialidades": [], "is_first_run": True}


def save_snapshot(especialidades):
    path = DATA_DIR / "last_snapshot.json"
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "especialidades": sorted(especialidades),
        "is_first_run": False
    }
    try:
        path.write_text(json.dumps(snapshot, indent=2), encoding='utf-8')
    except Exception:
        pass


def update_heartbeat(status="ok"):
    path = DATA_DIR / "heartbeat.json"
    heartbeat = {
        "last_run": datetime.now().isoformat(),
        "status": status,
    }
    try:
        path.write_text(json.dumps(heartbeat, indent=2), encoding='utf-8')
    except Exception:
        pass