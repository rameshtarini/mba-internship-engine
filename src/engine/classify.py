from __future__ import annotations

from .models import Posting


def classify_cycle(posting: Posting) -> str:
    text = f"{posting.role_title}\n{posting.raw_description}".lower()
    if "summer 2027" in text or "2027 summer" in text or "starting june 2027" in text or "class of 2028" in text:
        return "summer_2027"
    return "unstated"


def classify_mba(posting: Posting) -> tuple[str, str | None]:
    text = f"{posting.role_title}\n{posting.raw_description}"
    lower = text.lower()
    if "mba" in lower or "summer associate" in lower or "mba intern" in lower or "class of 2028" in lower:
        return "mba_required", "mba"
    if "mba or advanced degree preferred" in lower or "mba preferred" in lower:
        return "mba_preferred", "mba preferred"
    return "mba_unknown", None


def classify_track(posting: Posting) -> str:
    text = f"{posting.role_title}\n{posting.raw_description}".lower()
    if any(keyword in text for keyword in ["product manager", "technical product manager", "product management"]):
        return "product"
    if any(keyword in text for keyword in ["product strategy", "strategy & operations", "corp dev", "biz ops"]):
        return "product_strategy"
    if any(keyword in text for keyword in ["product marketing", "pmm"]):
        return "product_marketing"
    if "ai" in text or "machine learning" in text:
        return "ai_product"
    return "other_mba_tech"


def classify_posting(posting: Posting) -> Posting:
    posting.cycle = classify_cycle(posting)
    posting.track = classify_track(posting)
    posting.mba_preference, posting.mba_evidence = classify_mba(posting)
    return posting
