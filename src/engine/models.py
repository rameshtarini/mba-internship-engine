from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Company:
    name: str
    tier: str
    boards: list[dict[str, str]]
    careers_url: str
    notes: Optional[str] = None
    typical_open: Optional[str] = None


@dataclass
class Posting:
    id: str
    company: str
    role_title: str
    raw_description: str
    apply_url: str
    location: Optional[str] = None
    remote_flag: Optional[bool] = None
    posted_date: Optional[datetime] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    cycle: str = "unstated"
    track: str = "other_mba_tech"
    mba_evidence: Optional[str] = None
    mba_preference: Optional[str] = None
    sponsorship_flag: str = "unknown"
    deadline: Optional[str] = None
    tier: Optional[str] = None
    status: str = "open"
    closed_reason: Optional[str] = None
    my_status: str = "none"


@dataclass
class RunStats:
    boards_attempted: int = 0
    boards_succeeded: int = 0
    roles_found: int = 0
    duration_seconds: float = 0.0
