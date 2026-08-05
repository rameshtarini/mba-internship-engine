from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

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
                raw_description TEXT,
                apply_url TEXT,
                location TEXT,
                remote_flag TEXT,
                posted_date TEXT,
                first_seen_at TEXT,
                last_seen_at TEXT,
                cycle TEXT,
                track TEXT,
                mba_evidence TEXT,
                mba_preference TEXT,
                sponsorship_flag TEXT,
                deadline TEXT,
                tier TEXT,
                status TEXT,
                closed_reason TEXT,
                my_status TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS board_reads (
                board_key TEXT,
                run_count INTEGER,
                last_seen INTEGER,
                PRIMARY KEY (board_key)
            )
            """
        )
        self._connection.commit()
        # Migrate: add alerted column if missing; backfill existing rows so they don't trigger alerts.
        try:
            cursor.execute("ALTER TABLE postings ADD COLUMN alerted INTEGER DEFAULT 0")
            cursor.execute("UPDATE postings SET alerted = 1")
            self._connection.commit()
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def upsert_posting(self, posting: Posting) -> None:
        existing = self.get_posting(posting.id)
        payload = {
            "id": posting.id,
            "company": posting.company,
            "role_title": posting.role_title,
            "raw_description": posting.raw_description,
            "apply_url": posting.apply_url,
            "location": posting.location,
            "remote_flag": str(posting.remote_flag) if posting.remote_flag is not None else None,
            "posted_date": posting.posted_date.isoformat() if posting.posted_date else None,
            "first_seen_at": existing.first_seen_at if existing else self._now(),
            "last_seen_at": self._now(),
            "cycle": posting.cycle,
            "track": posting.track,
            "mba_evidence": posting.mba_evidence,
            "mba_preference": posting.mba_preference,
            "sponsorship_flag": posting.sponsorship_flag,
            "deadline": posting.deadline,
            "tier": posting.tier,
            "status": posting.status,
            "closed_reason": posting.closed_reason,
            "my_status": posting.my_status,
        }
        cursor = self._connection.cursor()
        cursor.execute(
            """
            INSERT INTO postings (
                id, company, role_title, raw_description, apply_url, location, remote_flag, posted_date,
                first_seen_at, last_seen_at, cycle, track, mba_evidence, mba_preference, sponsorship_flag,
                deadline, tier, status, closed_reason, my_status
            ) VALUES (
                :id, :company, :role_title, :raw_description, :apply_url, :location, :remote_flag, :posted_date,
                :first_seen_at, :last_seen_at, :cycle, :track, :mba_evidence, :mba_preference, :sponsorship_flag,
                :deadline, :tier, :status, :closed_reason, :my_status
            )
            ON CONFLICT(id) DO UPDATE SET
                company=excluded.company,
                role_title=excluded.role_title,
                raw_description=excluded.raw_description,
                apply_url=excluded.apply_url,
                location=excluded.location,
                remote_flag=excluded.remote_flag,
                posted_date=excluded.posted_date,
                last_seen_at=excluded.last_seen_at,
                cycle=excluded.cycle,
                track=excluded.track,
                mba_evidence=excluded.mba_evidence,
                mba_preference=excluded.mba_preference,
                sponsorship_flag=excluded.sponsorship_flag,
                deadline=excluded.deadline,
                tier=excluded.tier,
                status=excluded.status,
                closed_reason=excluded.closed_reason,
                my_status = CASE WHEN excluded.my_status != 'none' THEN excluded.my_status ELSE postings.my_status END
            """,
            payload,
        )
        self._connection.commit()

    def get_posting(self, posting_id: str) -> Posting | None:
        cursor = self._connection.cursor()
        row = cursor.execute("SELECT * FROM postings WHERE id = ?", (posting_id,)).fetchone()
        if not row:
            return None
        return self._row_to_posting(row)

    def list_postings(self, posting_id: str | None = None) -> int:
        cursor = self._connection.cursor()
        if posting_id:
            cursor.execute("SELECT COUNT(*) FROM postings WHERE id = ?", (posting_id,))
        else:
            cursor.execute("SELECT COUNT(*) FROM postings")
        return int(cursor.fetchone()[0])

    def _row_to_posting(self, row: tuple[object, ...]) -> Posting:
        return Posting(
            id=row[0],
            company=row[1] or "",
            role_title=row[2] or "",
            raw_description=row[3] or "",
            apply_url=row[4] or "",
            location=row[5],
            remote_flag=str(row[6]).lower() == "true" if row[6] is not None else None,
            posted_date=datetime.fromisoformat(row[7]) if row[7] else None,
            first_seen_at=datetime.fromisoformat(row[8]) if row[8] else None,
            last_seen_at=datetime.fromisoformat(row[9]) if row[9] else None,
            cycle=row[10] or "unstated",
            track=row[11] or "other_mba_tech",
            mba_evidence=row[12],
            mba_preference=row[13],
            sponsorship_flag=row[14] or "unknown",
            deadline=row[15],
            tier=row[16],
            status=row[17] or "open",
            closed_reason=row[18],
            my_status=row[19] or "none",
        )

    def sync_board(self, company_name: str, platform: str, slug: str, current_ids: list[str]) -> None:
        board_key = f"{company_name}:{platform}:{slug}"
        cursor = self._connection.cursor()
        row = cursor.execute("SELECT run_count, last_seen FROM board_reads WHERE board_key = ?", (board_key,)).fetchone()
        run_count = int(row[0]) if row else 0
        last_seen = int(row[1]) if row else 0

        current_ids_set = set(current_ids)
        existing_ids = {
            row[0]
            for row in cursor.execute("SELECT id FROM postings WHERE company = ?", (company_name,)).fetchall()
        }

        if current_ids_set == set(existing_ids) and run_count > 0:
            close_candidates = [
                row[0]
                for row in cursor.execute("SELECT id FROM postings WHERE company = ?", (company_name,)).fetchall()
                if row[0] not in current_ids_set
            ]
            if close_candidates:
                for posting_id in close_candidates:
                    self._mark_closed(posting_id, "gone_from_feed")
        elif run_count > 0:
            for posting_id in existing_ids - current_ids_set:
                self._mark_closed(posting_id, "gone_from_feed")

        cursor.execute(
            "INSERT INTO board_reads (board_key, run_count, last_seen) VALUES (?, ?, ?) ON CONFLICT(board_key) DO UPDATE SET run_count = excluded.run_count, last_seen = excluded.last_seen",
            (board_key, run_count + 1, int(datetime.now(timezone.utc).timestamp())),
        )
        self._connection.commit()

    def _mark_closed(self, posting_id: str, reason: str) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            "UPDATE postings SET status = ?, closed_reason = ? WHERE id = ?",
            ("closed", reason, posting_id),
        )
        self._connection.commit()

    def get_unalerted_tier_postings(self) -> list[Posting]:
        cursor = self._connection.cursor()
        rows = cursor.execute(
            "SELECT * FROM postings WHERE alerted = 0 AND tier IN ('Tier 1', 'Tier 2') AND status = 'open'"
        ).fetchall()
        return [self._row_to_posting(row) for row in rows]

    def mark_alerted(self, posting_id: str) -> None:
        cursor = self._connection.cursor()
        cursor.execute("UPDATE postings SET alerted = 1 WHERE id = ?", (posting_id,))
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()
