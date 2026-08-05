from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import Posting


def load_tracker(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {str(k): v for k, v in data.items() if isinstance(v, dict)}


def apply_tracker_to_posting(posting: Posting, tracker: dict[str, dict[str, Any]]) -> None:
    entry = tracker.get(posting.id)
    if entry and entry.get("my_status"):
        posting.my_status = str(entry["my_status"])
