from __future__ import annotations

import pathlib

import pytest
import yaml

from engine.classify import (
    classify_cycle,
    classify_mba,
    classify_posting,
    classify_track,
)
from engine.models import Posting

FIXTURES_DIR = pathlib.Path(__file__).resolve().parent / "fixtures"
FIXTURES_PATH = FIXTURES_DIR / "fixtures.yaml"


def load_fixtures() -> list[dict[str, str]]:
    with FIXTURES_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def make_posting(title: str, body: str) -> Posting:
    return Posting(
        id="fixture-test",
        company="TestCo",
        role_title=title,
        raw_description=body,
        apply_url="https://example.com",
    )


@pytest.mark.parametrize("case", load_fixtures())
def test_fixture_classification(case: dict[str, str]) -> None:
    body = (FIXTURES_DIR / case["file"]).read_text("utf-8")
    posting = make_posting(case["title"], body)
    classify_posting(posting)

    assert posting.cycle == case["expected_cycle"]
    assert posting.track == case["expected_track"]
    assert posting.mba_preference == case["expected_mba_preference"]
    if case.get("expected_mba_evidence") is None:
        assert posting.mba_evidence is None
    else:
        assert case["expected_mba_evidence"].lower() in posting.mba_evidence.lower()


def test_cycle_detector_handles_class_of_2028() -> None:
    posting = make_posting("Strategy Intern", "Class of 2028 candidates are encouraged to apply.")
    assert classify_cycle(posting) == "summer_2027"


def test_mba_preferred_vs_required_priority() -> None:
    posting = make_posting("Product Intern", "MBA or advanced degree preferred for this role.")
    preference, evidence = classify_mba(posting)
    assert preference == "mba_preferred"
    assert evidence.lower() == "mba or advanced degree preferred"


def test_track_ai_product_requires_ai_and_product_context() -> None:
    posting = make_posting("AI Product Intern", "Build machine learning products in the product organization.")
    assert classify_track(posting) == "ai_product"
