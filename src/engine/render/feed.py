from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ..models import Posting


def write_feed(path: Path, postings: Iterable[Posting]) -> None:
    path.write_text("<rss></rss>", encoding="utf-8")
