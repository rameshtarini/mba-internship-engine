from __future__ import annotations

import hashlib

import httpx

from ..fetch import Fetcher
from ..models import Posting


async def fetch_workday_postings(fetcher: Fetcher, company_name: str, company_slug: str) -> list[Posting]:
    url = f"https://{company_slug}.wd5.myworkdayjobs.com/wday/cxs/{company_slug}/{company_slug}-jobs"
    try:
        text = await fetcher.fetch_text(url)
    except httpx.HTTPError:
        return []

    postings: list[Posting] = []
    if "jobPosting" in text:
        postings.append(
            Posting(
                id=hashlib.sha256(f"{company_name}:workday".encode()).hexdigest(),
                company=company_name,
                role_title="Workday posting",
                raw_description=text[:1000],
                apply_url=url,
            )
        )
    return postings
