from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from .adapters.amazondotjobs import fetch_amazon_postings
from .adapters.applejobs import fetch_apple_postings
from .adapters.ashby import fetch_ashby_postings
from .adapters.googlecareers import fetch_google_postings
from .adapters.greenhouse import fetch_greenhouse_postings
from .adapters.lever import fetch_lever_postings
from .adapters.smartrecruiters import fetch_smartrecruiters_postings
from .adapters.workable import fetch_workable_postings
from .adapters.workday import fetch_workday_postings
from .classify import classify_posting
from .fetch import Fetcher
from .models import Company, Posting, RunStats
from .registry import load_companies
from .store import Store
from .tracker import apply_tracker_to_posting

ADAPTERS: dict[str, Any] = {
    "greenhouse": fetch_greenhouse_postings,
    "lever": fetch_lever_postings,
    "ashby": fetch_ashby_postings,
    "workday": fetch_workday_postings,
    "smartrecruiters": fetch_smartrecruiters_postings,
    "workable": fetch_workable_postings,
    "amazondotjobs": fetch_amazon_postings,
    "applejobs": fetch_apple_postings,
    "googlecareers": fetch_google_postings,
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


async def run_engine(
    companies_path: Path, tracker: dict | None = None
) -> tuple[list[Posting], RunStats]:
    companies = load_companies(companies_path)
    fetcher = Fetcher()
    stats = RunStats()
    tasks: list[asyncio.Task[list[Posting]]] = []
    store = Store(Path("data/engine.db"))

    for company in companies:
        if company.disabled:
            continue
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

    for posting in postings:
        if tracker:
            apply_tracker_to_posting(posting, tracker)
        store.upsert_posting(posting)

    for company in companies:
        if company.disabled:
            continue
        for board in company.boards:
            current_ids = [posting.id for posting in postings if posting.company == company.name]
            store.sync_board(company.name, board["platform"], board["slug"], current_ids)

    def _sort_key(p: Posting) -> tuple:
        dt = p.posted_date or p.first_seen_at
        if dt is not None and getattr(dt, "tzinfo", None) is not None:
            dt = dt.replace(tzinfo=None)
        return (dt or "", p.id)

    stats.roles_found = len(postings)
    postings.sort(key=_sort_key, reverse=True)
    store.close()
    return postings, stats
