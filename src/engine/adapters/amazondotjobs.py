from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import httpx

from ..fetch import Fetcher
from ..models import Posting

_SEARCH_URL = "https://www.amazon.jobs/en/search.json"
_BASE_URL = "https://www.amazon.jobs"

_QUERIES = ("MBA intern", "product manager intern", "Leadership Accelerator")


def _stable_id(job_id: str) -> str:
    return hashlib.sha256(f"amazon:{job_id}".encode()).hexdigest()


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    for fmt in ("%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


_US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC",
}


def _is_us(job: dict[str, Any]) -> bool:
    state = (job.get("state") or "").strip().upper()
    return state in _US_STATES


def _location(job: dict[str, Any]) -> str | None:
    city = job.get("city") or ""
    state = job.get("state") or ""
    if city and state:
        return f"{city}, {state}, United States"
    return job.get("location") or None


async def fetch_amazon_postings(fetcher: Fetcher, company_name: str, _slug: str) -> list[Posting]:
    seen: set[str] = set()
    postings: list[Posting] = []

    for query in _QUERIES:
        qs = urlencode({"base_query": query, "loc_query": "", "result_limit": 100, "sort": "recent"})
        url = f"{_SEARCH_URL}?{qs}&country%5B%5D=US"
        try:
            payload = await fetcher.fetch_json(url)
        except httpx.HTTPError:
            continue

        for job in payload.get("jobs", []) if isinstance(payload, dict) else []:
            job_id = str(job.get("id_icims", "")).strip()
            title_lower = job.get("title", "").lower()
            if not job_id or job_id in seen or not _is_us(job):
                continue
            if "intern" not in title_lower and "mba" not in title_lower:
                continue
            seen.add(job_id)
            job_path = job.get("job_path", "")
            apply_url = f"{_BASE_URL}{job_path}" if job_path else f"{_BASE_URL}/en/jobs/{job_id}"
            postings.append(
                Posting(
                    id=_stable_id(job_id),
                    company=company_name,
                    role_title=job.get("title", ""),
                    raw_description=job.get("description_short") or "",
                    apply_url=apply_url,
                    location=_location(job),
                    posted_date=_parse_date(job.get("posted_date")),
                )
            )

    return postings
