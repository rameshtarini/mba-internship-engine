from __future__ import annotations

import hashlib

from ..fetch import Fetcher
from ..models import Posting


async def fetch_lever_postings(fetcher: Fetcher, company_name: str, company_slug: str) -> list[Posting]:
    url = f"https://jobs.lever.co/{company_slug}?mode=json"
    payload = await fetcher.fetch_json(url)
    postings: list[Posting] = []

    for job in payload if isinstance(payload, list) else []:
        job_id = str(job.get("id") or job.get("title") or "")
        title = job.get("text", "") or job.get("title", "")
        raw_description = job.get("description", "") or ""
        apply_url = job.get("hostedUrl") or f"https://jobs.lever.co/{company_slug}/{job_id}"
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
