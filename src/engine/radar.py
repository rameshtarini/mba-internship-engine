from __future__ import annotations

from .models import Company


def compute_radar_status(company: Company) -> str:
    if company.typical_open:
        return "waiting"
    return "unknown"
