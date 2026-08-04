from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ..models import Posting


def write_feed(path: Path, postings: Iterable[Posting]) -> None:
    path.write_text("<rss></rss>", encoding="utf-8")
