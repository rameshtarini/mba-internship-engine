from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from ..models import Posting


def write_json(path: Path, postings: Iterable[Posting]) -> None:
    data = [posting.__dict__ for posting in postings]
    path.write_text(json.dumps(data, default=str, indent=2), encoding="utf-8")
