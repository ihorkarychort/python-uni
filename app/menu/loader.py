import yaml
from typing import Dict
from pathlib import Path

def load_yaml(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_all_menus(paths: Dict[str, str]) -> dict:
    return {
        "deals": load_yaml(paths["deals"]),
        "ingredients": load_yaml(paths["ingredients"]),
        "upsells": load_yaml(paths["upsells"]),
        "virtual": load_yaml(paths["virtual"]),
    }
