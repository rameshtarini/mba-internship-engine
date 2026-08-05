from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from ..models import Posting


def write_csv(path: Path, postings: Iterable[Posting]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "company", "role_title", "location", "cycle", "track", "mba_preference", "apply_url", "status"])
        for posting in postings:
            writer.writerow([
                posting.id,
                posting.company,
                posting.role_title,
                posting.location,
                posting.cycle,
                posting.track,
                posting.mba_preference,
                posting.apply_url,
                posting.status,
            ])
