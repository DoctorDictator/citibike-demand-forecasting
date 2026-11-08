from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "config.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    cfg_path = Path(path) if path else DEFAULT_CONFIG
    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["_project_root"] = str(PROJECT_ROOT)
    return cfg


def data_path(*parts: str, cfg: dict[str, Any] | None = None) -> Path:
    cfg = cfg or load_config()
    root = Path(cfg["_project_root"])
    path = root / cfg["project"]["data_dir"] / Path(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
