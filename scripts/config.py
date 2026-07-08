import json
import sys
from pathlib import Path


def get_config_path() -> Path:
    return Path(__file__).resolve().parent.parent / "obsidian-manager.json"


def load_config() -> dict:
    config_path = get_config_path()
    if not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        print("Run 'python scripts/obsidian_mgr.py init' to set up.", file=sys.stderr)
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")
