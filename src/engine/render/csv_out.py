from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from ..models import Posting


def write_csv(path: Path, postings: Iterable[Posting]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "company", "role_title", "apply_url", "status"])
        for posting in postings:
            writer.writerow([posting.id, posting.company, posting.role_title, posting.apply_url, posting.status])
