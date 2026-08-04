from __future__ import annotations

import yaml
from pathlib import Path

from .models import Company


def load_companies(path: Path | str) -> list[Company]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    companies = []
    for entry in raw or []:
        companies.append(Company(**entry))
    return companies
