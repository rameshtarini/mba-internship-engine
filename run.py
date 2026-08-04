import argparse

from engine import registry


def main() -> int:
    parser = argparse.ArgumentParser(description="MBA internship engine")
    parser.add_argument("--version", action="store_true", help="Show version")
    args = parser.parse_args()

    if args.version:
        print("mba-internship-engine 0.1.0")
        return 0

    print("MBA internship engine skeleton. Run `python -m pytest` after adding implementation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
