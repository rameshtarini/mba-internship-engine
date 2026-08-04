from __future__ import annotations

from pathlib import Path
import sqlite3

from .models import Posting


class Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._connection = sqlite3.connect(str(path))
        self._init_schema()

    def _init_schema(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS postings (
                id TEXT PRIMARY KEY,
                company TEXT,
                role_title TEXT,
                apply_url TEXT,
                status TEXT,
                first_seen_at TEXT,
                last_seen_at TEXT
            )
            """
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()
