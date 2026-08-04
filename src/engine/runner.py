from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from .adapters.greenhouse import fetch_greenhouse_postings
from .classify import classify_posting
from .fetch import Fetcher
from .models import Company, Posting, RunStats
from .registry import load_companies


ADAPTERS: dict[str, Any] = {
    "greenhouse": fetch_greenhouse_postings,
}


async def fetch_company_board(fetcher: Fetcher, company: Company, board: dict[str, str]) -> list[Posting]:
    platform = board["platform"]
    slug = board["slug"]
    adapter = ADAPTERS.get(platform)
    if adapter is None:
        raise ValueError(f"Unsupported board platform: {platform}")
    postings = await adapter(fetcher, company.name, slug)
    for posting in postings:
        posting.tier = company.tier
        classify_posting(posting)
    return postings


async def run_engine(companies_path: Path) -> tuple[list[Posting], RunStats]:
    companies = load_companies(companies_path)
    fetcher = Fetcher()
    stats = RunStats()
    tasks: list[asyncio.Task[list[Posting]]] = []

    for company in companies:
        for board in company.boards:
            stats.boards_attempted += 1
            tasks.append(asyncio.create_task(fetch_company_board(fetcher, company, board)))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    await fetcher.close()

    postings: list[Posting] = []
    for result in results:
        if isinstance(result, Exception):
            continue
        stats.boards_succeeded += 1
        postings.extend(result)

    stats.roles_found = len(postings)
    postings.sort(key=lambda posting: (posting.posted_date or posting.first_seen_at or posting.id), reverse=True)
    return postings, stats
