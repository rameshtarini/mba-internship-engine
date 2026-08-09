from __future__ import annotations

import re

from .models import Posting


def _normalize_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()


def _combine_text(posting: Posting) -> str:
    return f"{posting.role_title}\n{posting.raw_description}"


def _match_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(pattern)}\b", text) for pattern in patterns)


def classify_cycle(posting: Posting) -> str:
    text = _normalize_text(_combine_text(posting)).lower()
    if re.search(
        r"\b(summer\s+2027|2027\s+summer|summer\s+internship\s+2027|2027\s+summer\s+internship|starting\s+june\s+2027|graduating\s+2028|class\s+of\s+2028)\b",
        text,
    ):
        return "summer_2027"
    # Title-level "2027" combined with an internship keyword is sufficient evidence
    title = _normalize_text(posting.role_title or "").lower()
    if re.search(r"\b2027\b", title) and re.search(r"\bintern", title):
        return "summer_2027"
    return "unstated"


def classify_mba(posting: Posting) -> tuple[str, str | None]:
    text = _normalize_text(_combine_text(posting)).lower()
    preferred_patterns = [
        "mba or advanced degree preferred",
        "mba preferred",
    ]
    strong_positive_patterns = [
        "class of 2028",
        "summer associate",
        "graduate business students",
        "graduate business student",
        "pursuing an mba",
        "second-year graduate student",
        "mba intern",
        "mba",
    ]

    for pattern in preferred_patterns:
        if re.search(rf"\b{re.escape(pattern)}\b", text):
            return "mba_preferred", pattern

    for pattern in strong_positive_patterns:
        if re.search(rf"\b{re.escape(pattern)}\b", text):
            return "mba_required", pattern

    if re.search(r"\b(bachelor[’']?s degree required|rising junior|rising senior|undergraduate)\b", text):
        return "mba_unknown", None

    if re.search(r"\bbs/ms in computer science\b", text):
        return "mba_unknown", None

    if re.search(r"\b(apm|associate product manager)\b", text) and re.search(
        r"\b(new grad|entry[- ]level|early career|class of 202[78]|graduating 202[78])\b",
        text,
    ):
        return "mba_unknown", None

    return "mba_unknown", None


def classify_track(posting: Posting) -> str:
    text = _normalize_text(_combine_text(posting)).lower()
    ai_signal = bool(re.search(r"\b(ai|machine learning|machine-learning|ml)\b", text))
    product_patterns = [
        "product manager",
        "technical product manager",
        "product management",
        "product owner",
        "associate product manager",
        "product intern",
        "product associate",
        "product team",
        "apm",
    ]
    strategy_patterns = [
        "product strategy",
        "strategy & operations",
        "corp dev",
        "biz ops",
        "business operations",
    ]
    marketing_patterns = [
        "product marketing",
        "pmm",
        "marketing manager",
    ]

    if ai_signal and _match_any(text, product_patterns + strategy_patterns + marketing_patterns + ["product"]):
        return "ai_product"

    if _match_any(text, product_patterns):
        return "product"
    if _match_any(text, strategy_patterns):
        return "product_strategy"
    if _match_any(text, marketing_patterns):
        return "product_marketing"
    return "other_mba_tech"


def classify_posting(posting: Posting) -> Posting:
    posting.cycle = classify_cycle(posting)
    posting.track = classify_track(posting)
    posting.mba_preference, posting.mba_evidence = classify_mba(posting)
    return posting
