from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Company:
    name: str
    tier: str
    boards: list[dict[str, str]]
    careers_url: str
    notes: str | None = None
    typical_open: str | None = None
    disabled: bool = False


@dataclass
class Posting:
    id: str
    company: str
    role_title: str
    raw_description: str
    apply_url: str
    location: str | None = None
    remote_flag: bool | None = None
    posted_date: datetime | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    cycle: str = "unstated"
    track: str = "other_mba_tech"
    mba_evidence: str | None = None
    mba_preference: str | None = None
    sponsorship_flag: str = "unknown"
    deadline: str | None = None
    tier: str | None = None
    status: str = "open"
    closed_reason: str | None = None
    my_status: str = "none"


@dataclass
class RunStats:
    boards_attempted: int = 0
    boards_succeeded: int = 0
    roles_found: int = 0
    duration_seconds: float = 0.0
