from __future__ import annotations

from collections.abc import Iterable
from html import escape
from pathlib import Path

from ..models import Posting


def write_feed(path: Path, postings: Iterable[Posting]) -> None:
    items = []
    for posting in postings:
        title = escape(posting.role_title or "Untitled")
        company = escape(posting.company or "Unknown")
        description = escape((posting.raw_description or "")[:200])
        link = escape(posting.apply_url or "")
        items.append(
            f"<item><title>{company} — {title}</title><link>{link}</link><description>{description}</description></item>"
        )
    rss = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<rss version=\"2.0\">
  <channel>
    <title>MBA Internship Engine</title>
    <link>https://example.com</link>
    <description>Live MBA internship feed</description>
    {''.join(items)}
  </channel>
</rss>"""
    path.write_text(rss, encoding="utf-8")
