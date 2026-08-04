from __future__ import annotations

from typing import Iterable
from ..models import Posting


def render_readme(postings: Iterable[Posting]) -> str:
    lines = ["# MBA Internship Engine", "", "Generated README content goes here."]
    return "\n".join(lines)
