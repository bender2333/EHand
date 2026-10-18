import os
import json
import tomllib
from typing import Any, Dict, List, Optional

STATE_DIR = os.path.expanduser("~/.ehand")
ACTIVE_PERIPHERY_FILE = os.path.join(STATE_DIR, "active_periphery.json")
INJECTIONS_FILE = os.path.join(STATE_DIR, "active_injections.json")


def load_periphery_file(filepath: str) -> Dict[str, Any]:
    with open(filepath, "rb") as f:
        data = tomllib.load(f)
    return data


def save_active_periphery(data: Dict[str, Any]) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(ACTIVE_PERIPHERY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_active_periphery() -> Optional[Dict[str, Any]]:
    if not os.path.exists(ACTIVE_PERIPHERY_FILE):
        return None
    try:
        with open(ACTIVE_PERIPHERY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_active_injections(injections: List[Dict[str, Any]]) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(INJECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(injections, f, indent=2, ensure_ascii=False)


def get_active_injections() -> List[Dict[str, Any]]:
    if not os.path.exists(INJECTIONS_FILE):
        return []
    try:
        with open(INJECTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def add_injection(channel: str, kind: str, params: Dict[str, Any], persistent: bool = False) -> Dict[str, Any]:
    injections = get_active_injections()
    inj = {
        "id": f"inj_{len(injections)+1}_{int(os.times().system*1000)}",
        "channel": channel,
        "kind": kind,
        "params": params,
        "persistent": persistent,
    }
    injections.append(inj)
    save_active_injections(injections)
    return inj
