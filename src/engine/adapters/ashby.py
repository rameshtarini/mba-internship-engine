from __future__ import annotations

import hashlib

from ..fetch import Fetcher
from ..models import Posting


async def fetch_ashby_postings(fetcher: Fetcher, company_name: str, company_slug: str) -> list[Posting]:
    url = f"https://jobs.ashbyhq.com/api/non-user-facing/{company_slug}?include=details"
    payload = await fetcher.fetch_json(url)
    postings: list[Posting] = []
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []

    for job in jobs:
        job_id = str(job.get("id") or job.get("title") or "")
        title = job.get("title", "")
        raw_description = job.get("description", "") or ""
        apply_url = f"https://jobs.ashbyhq.com/{company_slug}/{job_id}"
        postings.append(
            Posting(
                id=hashlib.sha256(f"{company_name}:{job_id}".encode()).hexdigest(),
                company=company_name,
                role_title=title,
                raw_description=raw_description,
                apply_url=apply_url,
            )
        )
    return postings
