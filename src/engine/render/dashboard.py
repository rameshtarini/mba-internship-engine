from __future__ import annotations

from pathlib import Path


def write_dashboard(path: Path, postings: list[dict[str, str]]) -> None:
    html = "<!doctype html><html><head><meta charset='utf-8'><title>Dashboard</title></head><body><h1>Dashboard</h1></body></html>"
    path.write_text(html, encoding="utf-8")
