from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any

from ..fetch import Fetcher
from ..models import Posting

GREENHOUSE_BOARD_URL = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"


def _normalize_text(value: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _stable_id(company: str, greenhouse_id: int) -> str:
    payload = f"{company}:{greenhouse_id}".encode()
    return hashlib.sha256(payload).hexdigest()


def _parse_posted_date(job: dict[str, Any]) -> datetime | None:
    for key in ("created_at", "updated_at"):
        value = job.get(key)
        if value:
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                continue
    return None


def _parse_location(job: dict[str, Any]) -> tuple[str | None, bool | None]:
    location = job.get("location")
    if isinstance(location, dict):
        name = location.get("name")
    else:
        name = str(location) if location else None

    remote = False
    if name:
        lowered = name.lower()
        remote = "remote" in lowered or "virtual" in lowered
    return name, remote if name else None


async def fetch_greenhouse_postings(fetcher: Fetcher, company_name: str, company_slug: str) -> list[Posting]:
    url = GREENHOUSE_BOARD_URL.format(company=company_slug)
    payload = await fetcher.fetch_json(url)
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
    postings: list[Posting] = []

    for job in jobs:
        job_id = int(job["id"])
        title = job.get("title", "")
        raw_description = _normalize_text(job.get("content", ""))
        apply_url = job.get("absolute_url") or f"https://boards.greenhouse.io/{company_slug}/jobs/{job_id}"
        location, remote_flag = _parse_location(job)
        posted_date = _parse_posted_date(job)

        postings.append(
            Posting(
                id=_stable_id(company_name, job_id),
                company=company_name,
                role_title=title,
                raw_description=raw_description,
                apply_url=apply_url,
                location=location,
                remote_flag=remote_flag,
                posted_date=posted_date,
            )
        )

    return postings
