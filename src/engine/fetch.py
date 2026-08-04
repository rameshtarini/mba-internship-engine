from __future__ import annotations

import asyncio
import httpx
from typing import Any


class Fetcher:
    def __init__(self, concurrency: int = 6, timeout: int = 20) -> None:
        self._client = httpx.AsyncClient(timeout=timeout)
        self._semaphore = asyncio.Semaphore(concurrency)

    async def fetch_json(self, url: str) -> Any:
        async with self._semaphore:
            response = await self._client.get(url)
            response.raise_for_status()
            return response.json()

    async def fetch_text(self, url: str) -> str:
        async with self._semaphore:
            response = await self._client.get(url)
            response.raise_for_status()
            return response.text

    async def close(self) -> None:
        await self._client.aclose()
