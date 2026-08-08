from __future__ import annotations

from pathlib import Path

from engine.models import Posting
from engine.store import Store


def test_store_records_first_seen_and_dedupes(tmp_path: Path) -> None:
    path = tmp_path / "engine.db"
    store = Store(path)
    posting = Posting(
        id="abc123",
        company="TestCo",
        role_title="Product Intern",
        raw_description="MBA internship",
        apply_url="https://example.com/job",
    )

    store.upsert_posting(posting)
    first = store.get_posting("abc123")
    assert first is not None
    assert first.first_seen_at is not None
    assert first.status == "open"

    store.upsert_posting(posting)
    assert store.list_postings("abc123") == 1


def test_store_closes_missing_board_after_two_consecutive_runs(tmp_path: Path) -> None:
    path = tmp_path / "engine.db"
    store = Store(path)
    posting = Posting(
        id="close-me",
        company="TestCo",
        role_title="Strategy Intern",
        raw_description="MBA internship",
        apply_url="https://example.com/close",
    )

    store.upsert_posting(posting)
    store.sync_board("TestCo", "greenhouse", "testco", [])
    closed = store.get_posting("close-me")
    assert closed is not None
    assert closed.status == "open"

    store.sync_board("TestCo", "greenhouse", "testco", [])
    closed = store.get_posting("close-me")
    assert closed is not None
    assert closed.status == "closed"
    assert closed.closed_reason == "gone_from_feed"
