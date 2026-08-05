import argparse
import asyncio
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "src"))

from engine.alerts import fire_github_alerts
from engine.radar import compute_radar
from engine.registry import load_companies
from engine.render.csv_out import write_csv
from engine.render.dashboard import write_dashboard
from engine.render.feed import write_feed
from engine.render.json_api import write_json
from engine.render.readme import write_readme
from engine.runner import run_engine
from engine.store import Store
from engine.tracker import load_tracker


def main() -> int:
    parser = argparse.ArgumentParser(description="MBA internship engine")
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--companies", default="data/companies.yaml", help="Path to companies registry")
    parser.add_argument("--limit", type=int, default=10, help="Limit output postings")
    args = parser.parse_args()

    if args.version:
        print("mba-internship-engine 0.1.0")
        return 0

    companies_path = Path(args.companies)
    if not companies_path.exists():
        print(f"Companies registry not found: {companies_path}")
        return 1

    tracker_path = root / "data" / "my_tracker.yaml"
    tracker = load_tracker(tracker_path)

    print(f"Fetching from registry: {companies_path} ...")
    postings, stats = asyncio.run(run_engine(companies_path, tracker=tracker))
    print(f"Fetched {stats.roles_found} postings from {stats.boards_succeeded}/{stats.boards_attempted} boards")

    alert_store = Store(root / "data" / "engine.db")
    alerted = fire_github_alerts(postings, alert_store)
    alert_store.close()
    if alerted:
        print(f"Opened {alerted} GitHub Issue(s) for new Tier 1/2 postings")

    docs_dir = root / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "api").mkdir(exist_ok=True)

    us_postings = [p for p in postings if is_us_location(p.location)]
    output_postings = [p for p in us_postings if p.cycle == "summer_2027"]
    unstated_postings = [p for p in us_postings if p.cycle == "unstated"]

    print(f"Summer 2027 (stated, US): {len(output_postings)} | Cycle unstated (US): {len(unstated_postings)}")

    companies = load_companies(companies_path)
    radar_rows = compute_radar(companies, postings)
    live = sum(1 for r in radar_rows if r.status in ("live", "verified"))
    print(f"Radar: {live}/{len(radar_rows)} Tier 1/2 companies live")

    write_json(docs_dir / "api" / "jobs.json", output_postings)
    write_csv(root / "data" / "postings.csv", output_postings + unstated_postings)
    write_feed(docs_dir / "feed.xml", output_postings)
    write_dashboard(docs_dir / "index.html", output_postings, unstated_postings, radar_rows)
    write_readme(root / "README.md", output_postings, unstated_postings, radar_rows, stats)

    for posting in output_postings[: args.limit]:
        print("---")
        print(f"Company: {posting.company}")
        print(f"Role: {posting.role_title}")
        print(f"Cycle: {posting.cycle}")
        print(f"Track: {posting.track}")
        print(f"MBA evidence: {posting.mba_evidence}")
        print(f"MBA preference: {posting.mba_preference}")
        print(f"Location: {posting.location}")
        print(f"Apply URL: {posting.apply_url}")
        print(f"Posted date: {posting.posted_date}")
    return 0


def is_us_location(location: str | None) -> bool:
    if not location:
        return False

    text = location.lower()
    us_keywords = [
        "united states",
        "united states of america",
        "usa",
        "u.s.",
        "u.s.a.",
        "remote - united states",
        "remote (us)",
        "remote (usa)",
        "remote us",
        "us remote",
        "washington, d.c.",
        "washington d.c.",
        "washington dc",
        "district of columbia",
        "d.c.",
    ]
    if any(keyword in text for keyword in us_keywords):
        return True

    states = [
        "alabama","alaska","arizona","arkansas","california","colorado","connecticut","delaware","florida",
        "georgia","hawaii","idaho","illinois","indiana","iowa","kansas","kentucky","louisiana","maine",
        "maryland","massachusetts","michigan","minnesota","mississippi","missouri","montana","nebraska",
        "nevada","new hampshire","new jersey","new mexico","new york","north carolina","north dakota","ohio",
        "oklahoma","oregon","pennsylvania","rhode island","south carolina","south dakota","tennessee","texas",
        "utah","vermont","virginia","washington","west virginia","wisconsin","wyoming","district of columbia",
    ]
    if any(state in text for state in states):
        return True

    abbrevs = [
        "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA",
        "ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH",
        "OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC",
    ]
    abbrev_pattern = r"\b(?:" + "|".join(abbrevs) + r")\b"
    if re.search(abbrev_pattern, location):
        return True

    return False


if __name__ == "__main__":
    sys.exit(main())
