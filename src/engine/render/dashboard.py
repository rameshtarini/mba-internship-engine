from __future__ import annotations

from html import escape
from pathlib import Path

from ..models import Posting


def write_dashboard(path: Path, postings: list[Posting]) -> None:
    cards = []
    for posting in postings:
        posted = posting.posted_date.strftime("%Y-%m-%d") if posting.posted_date else "—"
        track = escape(posting.track or "other_mba_tech")
        title = escape(posting.role_title or "Untitled")
        company = escape(posting.company or "Unknown")
        evidence = escape(posting.mba_evidence or "—")
        preference = escape(posting.mba_preference or "mba_unknown")
        cards.append(
            f"""
            <article class=\"card\" data-company=\"{escape(posting.company or 'Unknown')}\" data-track=\"{track}\" data-mba=\"{preference}\">
              <h3>{company} — {title}</h3>
              <p><strong>Track:</strong> {track}</p>
              <p><strong>MBA:</strong> {preference}</p>
              <p><strong>Evidence:</strong> {evidence}</p>
              <p><strong>Cycle:</strong> {escape(posting.cycle or 'unstated')}</p>
              <p><strong>Posted:</strong> {posted}</p>
              <p><a href=\"{escape(posting.apply_url)}\" target=\"_blank\" rel=\"noreferrer\">Apply</a></p>
            </article>
            """
        )

    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>MBA Internship Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; background: #f7f7fb; color: #1f2937; }}
    h1 {{ margin-bottom: 0.25rem; }}
    .toolbar {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }}
    input, select {{ padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 6px; }}
    .card {{ background: white; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    a {{ color: #2563eb; }}
  </style>
</head>
<body>
  <h1>MBA Internship Dashboard</h1>
  <p>{len(postings)} postings generated locally.</p>
  <div class=\"toolbar\">
    <input id=\"search\" type=\"text\" placeholder=\"Search company or role\" />
    <select id=\"trackFilter\">
      <option value=\"all\">All tracks</option>
      <option value=\"product\">Product</option>
      <option value=\"product_strategy\">Product Strategy</option>
      <option value=\"product_marketing\">Product Marketing</option>
      <option value=\"ai_product\">AI Product</option>
      <option value=\"other_mba_tech\">Other MBA Tech</option>
    </select>
    <select id=\"mbaFilter\">
      <option value=\"all\">All MBA levels</option>
      <option value=\"mba_required\">MBA required</option>
      <option value=\"mba_preferred\">MBA preferred</option>
      <option value=\"mba_unknown\">MBA unknown</option>
    </select>
  </div>
  <div id=\"cards\">{''.join(cards)}</div>
  <script>
    const searchInput = document.getElementById('search');
    const trackFilter = document.getElementById('trackFilter');
    const mbaFilter = document.getElementById('mbaFilter');
    const cards = Array.from(document.querySelectorAll('.card'));
    function applyFilters() {{
      const query = searchInput.value.trim().toLowerCase();
      const track = trackFilter.value;
      const mba = mbaFilter.value;
      cards.forEach((card) => {{
        const text = (card.textContent || '').toLowerCase();
        const matchQuery = !query || text.includes(query);
        const matchTrack = track === 'all' || card.dataset.track === track;
        const matchMba = mba === 'all' || card.dataset.mba === mba;
        card.style.display = matchQuery && matchTrack && matchMba ? 'block' : 'none';
      }});
    }}
    [searchInput, trackFilter, mbaFilter].forEach((element) => element.addEventListener('input', applyFilters));
    applyFilters();
  </script>
</body>
</html>"""
    path.write_text(html, encoding="utf-8")
