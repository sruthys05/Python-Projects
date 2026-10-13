import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import requests

from .scraper import GithubProfileScraper


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract publicly visible information from a GitHub profile."
    )
    parser.add_argument("username", help="GitHub username to look up")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("github_profile.json"),
        help="JSON output path (default: github_profile.json)",
    )
    args = parser.parse_args()

    try:
        profile = GithubProfileScraper().scrape(args.username)
        args.output.write_text(
            json.dumps(asdict(profile), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except (requests.RequestException, OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Saved public profile data to {args.output}")
    return 0
