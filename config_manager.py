import json
import os

CONFIG_FILE = "system_config.json"

DEFAULT_CONFIG = {
    "threshold": 78,
    "shift_ratio": 0.07,
    "system_enabled": True
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)