from __future__ import annotations

import re
from html import escape
from pathlib import Path
from typing import TYPE_CHECKING

from ..models import Posting

if TYPE_CHECKING:
    from ..radar import RadarRow


def extract_city(location: str | None) -> str:
    if not location:
        return ""
    loc = location.strip()
    if re.match(r"^remote\b", loc, re.IGNORECASE):
        return "Remote"
    first_part = loc.split(",")[0].strip()
    return first_part


_STATUS_COLORS = {
    "watching": "#2563eb",
    "applied": "#d97706",
    "interviewing": "#7c3aed",
    "offer": "#16a34a",
    "rejected": "#dc2626",
    "passed": "#6b7280",
}


def _make_card(posting: Posting) -> str:
    posted = posting.posted_date.strftime("%Y-%m-%d") if posting.posted_date else "—"
    track = escape(posting.track or "other_mba_tech")
    title = escape(posting.role_title or "Untitled")
    company = escape(posting.company or "Unknown")
    evidence = escape(posting.mba_evidence or "—")
    preference = escape(posting.mba_preference or "mba_unknown")
    location_str = escape(posting.location or "—")
    city = escape(extract_city(posting.location))
    tier = escape(posting.tier or "")
    my_status = posting.my_status or "none"
    badge = ""
    if my_status and my_status != "none":
        color = _STATUS_COLORS.get(my_status, "#6b7280")
        badge = (
            f' <span style="display:inline-block;padding:2px 8px;border-radius:9999px;'
            f'background:{color};color:#fff;font-size:0.75rem;font-weight:600;'
            f'vertical-align:middle">{escape(my_status)}</span>'
        )
    return (
        f'<article class="card" '
        f'data-company="{escape(posting.company or "Unknown")}" '
        f'data-track="{track}" '
        f'data-mba="{preference}" '
        f'data-city="{city}">\n'
        f"  <h3>{company} &mdash; {title}{badge}</h3>\n"
        f"  <p><strong>Track:</strong> {track} &nbsp; <strong>MBA:</strong> {preference}"
        + (f" &nbsp; <strong>Tier:</strong> {tier}" if tier else "")
        + f"</p>\n"
        f"  <p><strong>Location:</strong> {location_str}</p>\n"
        f"  <p><strong>Evidence:</strong> <em>{evidence}</em></p>\n"
        f"  <p><strong>Posted:</strong> {posted}</p>\n"
        f'  <p><a href="{escape(posting.apply_url)}" target="_blank" rel="noreferrer">Apply &rarr;</a></p>\n'
        f"</article>\n"
    )


def _radar_html(rows: list[RadarRow]) -> str:
    if not rows:
        return ""
    status_icon = {"verified": "🎯", "live": "✅", "waiting": "⏳"}
    status_label = {"verified": "live-verified", "live": "live", "waiting": "waiting"}
    row_html = []
    for r in rows:
        icon = status_icon.get(r.status, "")
        cls = status_label.get(r.status, "")
        if r.status == "verified":
            detail = f"{icon} Live since {r.verified_date} ({r.live_count} roles)"
        elif r.status == "live":
            detail = f"{icon} Live ({r.live_count} roles)"
        else:
            detail = f"{icon} Waiting"
        row_html.append(
            f'<tr class="radar-{cls}">'
            f"<td>{escape(r.company)}</td>"
            f"<td>{escape(r.tier)}</td>"
            f"<td>{escape(r.typical_open or '—')}</td>"
            f"<td>{detail}</td>"
            f"</tr>"
        )
    return (
        '<table class="radar">'
        "<thead><tr><th>Company</th><th>Tier</th><th>Expected</th><th>Status</th></tr></thead>"
        "<tbody>" + "".join(row_html) + "</tbody>"
        "</table>"
    )


def write_dashboard(
    path: Path,
    postings: list[Posting],
    unstated_postings: list[Posting] | None = None,
    radar_rows: list[RadarRow] | None = None,
) -> None:
    if unstated_postings is None:
        unstated_postings = []
    if radar_rows is None:
        radar_rows = []

    all_postings = postings + unstated_postings

    cities = sorted({c for p in all_postings if (c := extract_city(p.location))})
    city_options = "\n".join(
        f'        <option value="{escape(c)}">{escape(c)}</option>' for c in cities if c
    )

    stated_cards = "".join(_make_card(p) for p in postings)
    unstated_cards = "".join(_make_card(p) for p in unstated_postings)

    stated_count = len(postings)
    unstated_count = len(unstated_postings)
    total = stated_count + unstated_count

    unstated_section = ""
    if unstated_postings:
        unstated_section = f"""
  <section>
    <h2>Cycle Not Stated &mdash; {unstated_count} postings</h2>
    <p class="note">These do not explicitly mention Summer 2027 but are MBA-level PM roles at tracked companies. Per the spec, postings from Aug 2026 onward are surfaced even without a stated cycle.</p>
    <div>{unstated_cards}</div>
  </section>"""

    radar_section = ""
    if radar_rows:
        radar_section = f"""
  <section>
    <h2>🎯 Drop Radar &mdash; Tier 1 &amp; Tier 2</h2>
    <p class="note">Typical opening dates are estimates. Once a real posting appears the date is verified (🎯).</p>
    {_radar_html(radar_rows)}
  </section>"""

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>MBA Internship Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; background: #f7f7fb; color: #1f2937; max-width: 980px; }}
    h1 {{ margin-bottom: 0.25rem; }}
    h2 {{ margin-top: 2rem; margin-bottom: 0.25rem; }}
    .note {{ color: #6b7280; font-size: 0.875rem; margin: 0.25rem 0 1rem; }}
    .toolbar {{ display: flex; gap: 0.75rem; flex-wrap: wrap; margin: 1rem 0 1.5rem; }}
    input, select {{ padding: 0.45rem 0.6rem; border: 1px solid #d1d5db; border-radius: 6px; font-size: 0.875rem; }}
    .card {{ background: white; border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 0.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
    .card h3 {{ margin: 0 0 0.5rem; font-size: 1rem; }}
    .card p {{ margin: 0.2rem 0; font-size: 0.875rem; }}
    a {{ color: #2563eb; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    section {{ margin-bottom: 2rem; }}
    table.radar {{ border-collapse: collapse; width: 100%; font-size: 0.875rem; margin-top: 0.5rem; }}
    table.radar th {{ background: #f3f4f6; text-align: left; padding: 0.4rem 0.75rem; border-bottom: 2px solid #e5e7eb; }}
    table.radar td {{ padding: 0.4rem 0.75rem; border-bottom: 1px solid #f3f4f6; }}
    tr.radar-live-verified {{ background: #f0fdf4; }}
    tr.radar-live {{ background: #fffbeb; }}
    tr.radar-waiting {{ color: #6b7280; }}
  </style>
</head>
<body>
  <h1>MBA Internship Dashboard</h1>
  <p class="note">{total} US postings &mdash; public employer career feeds only &mdash; not a substitute for 12twenty/Handshake</p>{radar_section}
  <div class="toolbar">
    <input id="search" type="text" placeholder="Search company or role&hellip;" style="min-width:200px" />
    <select id="trackFilter">
      <option value="all">All tracks</option>
      <option value="product">Product</option>
      <option value="product_strategy">Product Strategy</option>
      <option value="product_marketing">Product Marketing</option>
      <option value="ai_product">AI Product</option>
      <option value="other_mba_tech">Other MBA Tech</option>
    </select>
    <select id="mbaFilter">
      <option value="all">All MBA levels</option>
      <option value="mba_required">MBA required</option>
      <option value="mba_preferred">MBA preferred</option>
      <option value="mba_unknown">MBA unknown</option>
    </select>
    <select id="cityFilter">
      <option value="all">All cities</option>
{city_options}
    </select>
  </div>
  <section>
    <h2>Summer 2027 &mdash; Explicitly Stated &mdash; {stated_count} postings</h2>
    <div>{stated_cards}</div>
  </section>{unstated_section}
  <script>
    const searchEl = document.getElementById('search');
    const trackEl = document.getElementById('trackFilter');
    const mbaEl = document.getElementById('mbaFilter');
    const cityEl = document.getElementById('cityFilter');
    const cards = Array.from(document.querySelectorAll('.card'));
    function applyFilters() {{
      const q = searchEl.value.trim().toLowerCase();
      const track = trackEl.value;
      const mba = mbaEl.value;
      const city = cityEl.value;
      cards.forEach(card => {{
        const text = (card.textContent || '').toLowerCase();
        const ok =
          (!q || text.includes(q)) &&
          (track === 'all' || card.dataset.track === track) &&
          (mba === 'all' || card.dataset.mba === mba) &&
          (city === 'all' || card.dataset.city === city);
        card.style.display = ok ? '' : 'none';
      }});
    }}
    [searchEl, trackEl, mbaEl, cityEl].forEach(el => el.addEventListener('input', applyFilters));
    applyFilters();
  </script>
</body>
</html>"""
    path.write_text(html, encoding="utf-8")
