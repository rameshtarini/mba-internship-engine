from __future__ import annotations

import hashlib

from ..fetch import Fetcher
from ..models import Posting


async def fetch_smartrecruiters_postings(fetcher: Fetcher, company_name: str, company_slug: str) -> list[Posting]:
    url = f"https://api.smartrecruiters.com/v1/companies/{company_slug}/postings"
    payload = await fetcher.fetch_json(url)
    postings: list[Posting] = []
    for job in payload.get("content", []) if isinstance(payload, dict) else []:
        title = job.get("title", "")
        raw_description = job.get("jobAd", "") or ""
        apply_url = job.get("applyUrl") or f"https://jobs.smartrecruiters.com/{company_slug}/{job.get('id', '')}"
        postings.append(
            Posting(
                id=hashlib.sha256(f"{company_name}:{job.get('id', title)}".encode()).hexdigest(),
                company=company_name,
                role_title=title,
                raw_description=raw_description,
                apply_url=apply_url,
            )
        )
    return postings
