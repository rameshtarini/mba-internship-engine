from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime

import httpx

from ..fetch import Fetcher
from ..models import Posting

_SEARCH_URL = "https://jobs.apple.com/en-us/search?search=MBA+internship&sort=relevance&team=STDNT"
_DETAIL_BASE = "https://jobs.apple.com/en-us/details"

_HYDRATION_RE = re.compile(
    r'window\.__staticRouterHydrationData\s*=\s*JSON\.parse\("(.+?)"\);\s*</script>',
    re.DOTALL,
)


def _stable_id(job_id: str) -> str:
    return hashlib.sha256(f"apple:{job_id}".encode()).hexdigest()


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    for fmt in ("%b %d, %Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str.strip()[:19], fmt)
        except (ValueError, TypeError):
            continue
    return None


def _location(job: dict) -> str | None:
    locs = job.get("locations", [])
    if not locs:
        return None
    parts = []
    for loc in locs[:3]:
        city = loc.get("city", "")
        state = loc.get("stateProvince", "")
        country = loc.get("countryName", "")
        if city and state:
            parts.append(f"{city}, {state}")
        elif city:
            parts.append(city)
        elif country:
            parts.append(country)
    return "; ".join(parts) or None


def _extract_results(html: str) -> list[dict]:
    m = _HYDRATION_RE.search(html)
    if not m:
        return []
    raw = m.group(1)
    try:
        data_str = json.loads(f'"{raw}"')
        hydration = json.loads(data_str)
    except (json.JSONDecodeError, ValueError):
        return []
    return (
        hydration.get("loaderData", {})
        .get("search", {})
        .get("searchResults", [])
    )


def _is_us_mba(job: dict) -> bool:
    title = job.get("postingTitle", "").lower()
    locs = job.get("locations", [])
    is_us = any(
        "united states" in loc.get("countryName", "").lower() for loc in locs
    )
    is_relevant = "mba" in title or ("intern" in title and "mba" in job.get("jobSummary", "").lower())
    return is_us and is_relevant


async def fetch_apple_postings(fetcher: Fetcher, company_name: str, _slug: str) -> list[Posting]:
    try:
        html = await fetcher.fetch_text(_SEARCH_URL)
    except httpx.HTTPError:
        return []

    raw_results = _extract_results(html)
    postings: list[Posting] = []
    for job in raw_results:
        if not _is_us_mba(job):
            continue
        pos_id = str(job.get("positionId") or "").strip()
        if not pos_id:
            continue
        slug = job.get("transformedPostingTitle") or re.sub(r"[^a-z0-9]+", "-", job.get("postingTitle", "").lower()).strip("-")
        apply_url = f"{_DETAIL_BASE}/{pos_id}/{slug}"
        postings.append(
            Posting(
                id=_stable_id(pos_id),
                company=company_name,
                role_title=job.get("postingTitle", ""),
                raw_description=job.get("jobSummary") or "",
                apply_url=apply_url,
                location=_location(job),
                posted_date=_parse_date(job.get("postingDate") or job.get("postDateInGMT")),
            )
        )
    return postings
