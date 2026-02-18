import json
from datetime import datetime
from pathlib import Path

# Garante que o caminho seja relativo ao pacote ou execução
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def load_snapshot():
    path = DATA_DIR / "last_snapshot.json"
    
    if not path.exists():
        return {"especialidades": []}
    
    try:
        content = path.read_text(encoding='utf-8').strip()
        if not content:
            # Arquivo existe mas está vazio
            return {"especialidades": []}
        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        # Arquivo corrompido, retorna estado vazio para não travar o bot
        print("⚠️ Aviso: Snapshot corrompido. Iniciando novo estado.")
        return {"especialidades": []}


def save_snapshot(especialidades):
    path = DATA_DIR / "last_snapshot.json"
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "especialidades": sorted(especialidades),
    }
    try:
        path.write_text(json.dumps(snapshot, indent=2), encoding='utf-8')
    except Exception as e:
        print(f"Erro ao salvar snapshot: {e}")


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