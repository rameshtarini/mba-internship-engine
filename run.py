import argparse
import asyncio
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "src"))

from engine.render.csv_out import write_csv
from engine.render.dashboard import write_dashboard
from engine.render.feed import write_feed
from engine.render.json_api import write_json
from engine.runner import run_engine


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

    postings, stats = asyncio.run(run_engine(companies_path))
    print(f"Fetched {stats.roles_found} postings from {stats.boards_succeeded}/{stats.boards_attempted} boards")

    docs_dir = root / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "api").mkdir(exist_ok=True)

    write_json(docs_dir / "api" / "jobs.json", postings)
    write_csv(root / "data" / "postings.csv", postings)
    write_feed(docs_dir / "feed.xml", postings)
    write_dashboard(docs_dir / "index.html", postings)

    for posting in postings[: args.limit]:
        print("---")
        print(f"Company: {posting.company}")
        print(f"Role: {posting.role_title}")
        print(f"Cycle: {posting.cycle}")
        print(f"Track: {posting.track}")
        print(f"MBA evidence: {posting.mba_evidence}")
        print(f"MBA preference: {posting.mba_preference}")
        print(f"Apply URL: {posting.apply_url}")
        print(f"Posted date: {posting.posted_date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
