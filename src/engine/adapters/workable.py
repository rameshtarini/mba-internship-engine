from __future__ import annotations

import hashlib

import httpx

from ..fetch import Fetcher
from ..models import Posting


async def fetch_workable_postings(fetcher: Fetcher, company_name: str, company_slug: str) -> list[Posting]:
    url = f"https://jobs.workable.com/api/v1/companies/{company_slug}/jobs"
    try:
        payload = await fetcher.fetch_json(url)
    except httpx.HTTPError:
        return []
    postings: list[Posting] = []
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
    for job in jobs:
        title = job.get("title", "")
        raw_description = job.get("description", "") or ""
        apply_url = job.get("apply_url") or f"https://apply.workable.com/{company_slug}/"
        postings.append(
            Posting(
                id=hashlib.sha256(f"{company_name}:{job.get('shortcode', title)}".encode()).hexdigest(),
                company=company_name,
                role_title=title,
                raw_description=raw_description,
                apply_url=apply_url,
            )
        )
    return postings
