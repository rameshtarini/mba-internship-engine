from __future__ import annotations

import asyncio
from typing import Any

import httpx


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


class Fetcher:
    def __init__(self, concurrency: int = 6, timeout: int = 20) -> None:
        self._client = httpx.AsyncClient(timeout=timeout, headers=_HEADERS)
        self._semaphore = asyncio.Semaphore(concurrency)

    async def fetch_json(self, url: str) -> Any:
        async with self._semaphore:
            response = await self._client.get(url)
            response.raise_for_status()
            return response.json()

    async def post_json(self, url: str, body: Any) -> Any:
        async with self._semaphore:
            response = await self._client.post(url, json=body)
            response.raise_for_status()
            return response.json()

    async def fetch_text(self, url: str) -> str:
        async with self._semaphore:
            response = await self._client.get(url)
            response.raise_for_status()
            return response.text

    async def close(self) -> None:
        await self._client.aclose()
