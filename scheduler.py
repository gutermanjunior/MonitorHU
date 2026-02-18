from datetime import datetime
import yaml


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def get_interval_minutes():
    config = load_config()
    now = datetime.now()
    hour = now.hour

    for block in config["intervals"].values():
        if block["start"] <= hour < block["end"]:
            return block["minutes"]

    return 60
