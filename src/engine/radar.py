from __future__ import annotations

from dataclasses import dataclass

from .models import Company, Posting

_MONTH_ORDER = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}


@dataclass
class RadarRow:
    company: str
    tier: str
    typical_open: str | None
    status: str  # "waiting" | "live" | "verified"
    verified_date: str | None
    live_count: int


def compute_radar(companies: list[Company], postings: list[Posting]) -> list[RadarRow]:
    tracked = [c for c in companies if c.tier in ("Tier 1", "Tier 2")]

    open_by_company: dict[str, list[Posting]] = {}
    for p in postings:
        if p.status == "open":
            open_by_company.setdefault(p.company, []).append(p)

    rows: list[RadarRow] = []
    for company in tracked:
        live = open_by_company.get(company.name, [])
        if live:
            with_date = [p for p in live if p.posted_date]
            if with_date:
                earliest = min(p.posted_date for p in with_date)  # type: ignore[type-var]
                status = "verified"
                verified_date = earliest.strftime("%Y-%m-%d")
            else:
                status = "live"
                verified_date = None
        else:
            status = "waiting"
            verified_date = None

        rows.append(RadarRow(
            company=company.name,
            tier=company.tier,
            typical_open=company.typical_open,
            status=status,
            verified_date=verified_date,
            live_count=len(live),
        ))

    def _sort_key(row: RadarRow) -> tuple[int, int]:
        status_order = {"verified": 0, "live": 1, "waiting": 2}
        month = _MONTH_ORDER.get(row.typical_open or "", 99)
        return (status_order.get(row.status, 9), month)

    return sorted(rows, key=_sort_key)
