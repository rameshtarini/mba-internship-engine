from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from ..fetch import Fetcher
from ..models import Posting

_BASE = "https://careers.google.com"
_SEARCH_URL = (
    _BASE + "/jobs/results/?q={query}&location=United+States&sort_by=date"
)
_QUERIES = ("MBA intern", "product manager intern 2027")

_CALLBACK_RE = re.compile(
    r"AF_initDataCallback\(\s*\{[^}]*?key\s*:\s*['\"]ds:1['\"].*?data\s*:\s*(\[.*?\])\s*,\s*sideChannel",
    re.DOTALL,
)


def _stable_id(job_id: str) -> str:
    return hashlib.sha256(f"google:{job_id}".encode()).hexdigest()


def _extract_jobs(html: str) -> list[Any]:
    m = _CALLBACK_RE.search(html)
    if not m:
        return []
    try:
        outer = json.loads(m.group(1))
        return outer[0] or []
    except (json.JSONDecodeError, IndexError, TypeError):
        return []


def _location(job: list) -> str | None:
    try:
        locs = job[9]
        if locs:
            return "; ".join(str(loc) for loc in locs[:3])
    except (IndexError, TypeError):
        pass
    return None


def _apply_url(job: list, job_id: str) -> str:
    try:
        url = str(job[2] or "").strip()
        if url and url.startswith("http"):
            return url
    except (IndexError, TypeError):
        pass
    return f"{_BASE}/jobs/results/{job_id}"


def _posted_date(job: list) -> datetime | None:
    try:
        ts = job[14]
        if ts:
            return datetime.fromtimestamp(int(ts), tz=timezone.utc).replace(tzinfo=None)
    except (IndexError, TypeError, ValueError, OSError):
        pass
    return None


async def fetch_google_postings(fetcher: Fetcher, company_name: str, _slug: str) -> list[Posting]:
    seen: set[str] = set()
    postings: list[Posting] = []

    for query in _QUERIES:
        url = _SEARCH_URL.format(query=query.replace(" ", "+"))
        try:
            html = await fetcher.fetch_text(url)
        except httpx.HTTPError:
            continue

        for job in _extract_jobs(html):
            try:
                job_id = str(job[0] or "").strip()
                title = str(job[1] or "").strip()
            except (IndexError, TypeError):
                continue

            if not job_id or job_id in seen:
                continue
            if "intern" not in title.lower():
                continue

            seen.add(job_id)
            postings.append(
                Posting(
                    id=_stable_id(job_id),
                    company=company_name,
                    role_title=title,
                    raw_description="",
                    apply_url=_apply_url(job, job_id),
                    location=_location(job),
                    posted_date=_posted_date(job),
                )
            )

    return postings
