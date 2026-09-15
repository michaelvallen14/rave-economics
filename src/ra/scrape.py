"""Part A acquisition: scrape Australian rave/dance-event listings from
every source that passed feasibility (see IMPORTANT_NOTES.md and the
docs/*-feasibility.md reports) and persist them to a local DuckDB
database under data/ — never committed, per the project's data-handling
rules.

Combines:
- Moshtix (scrape_moshtix.py) — crawled directly, Australia-wide
- Ticketbooth/Leap Events, Ticket Merchant, Megatix (scrape_seeded.py) —
  seeded from src/ra/seeds.py, since none of the three has a crawlable
  listing page

Run: uv run python -m src.ra.scrape --moshtix-limit 200
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

import duckdb
import httpx

from src.ra.common import FetchLog, dedupe_records, status_counts
from src.ra.scrape_moshtix import USER_AGENT, TIMEOUT_SECONDS
from src.ra.scrape_moshtix import fetch_events as fetch_moshtix_events
from src.ra.scrape_seeded import fetch_seeded_events

DEFAULT_DB_PATH = "data/raw/ra/events.duckdb"


def write_events(db_path: str, records) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS ra_events (
                url TEXT PRIMARY KEY,
                date TEXT,
                name TEXT,
                venue TEXT,
                city TEXT,
                region TEXT,
                lineup TEXT,
                promoter TEXT,
                genre_tags TEXT,
                price TEXT,
                attendance_indicator TEXT,
                source TEXT
            )
            """
        )
        rows = [asdict(r) for r in records]
        con.executemany(
            """
            INSERT INTO ra_events VALUES
                ($url, $date, $name, $venue, $city, $region, $lineup,
                 $promoter, $genre_tags, $price, $attendance_indicator, $source)
            ON CONFLICT (url) DO UPDATE SET
                date = excluded.date,
                name = excluded.name,
                venue = excluded.venue,
                city = excluded.city,
                region = excluded.region,
                lineup = excluded.lineup,
                promoter = excluded.promoter,
                genre_tags = excluded.genre_tags,
                price = excluded.price,
                attendance_indicator = excluded.attendance_indicator,
                source = excluded.source
            """,
            rows,
        )
    finally:
        con.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--moshtix-limit", type=int, default=200)
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--skip-moshtix", action="store_true")
    parser.add_argument("--skip-seeded", action="store_true")
    args = parser.parse_args()

    log: list[FetchLog] = []
    headers = {"User-Agent": USER_AGENT}
    records = []
    with httpx.Client(headers=headers, timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
        if not args.skip_moshtix:
            records += fetch_moshtix_events(client, args.moshtix_limit, log)
        if not args.skip_seeded:
            records += fetch_seeded_events(client, log)

    records = dedupe_records(records)
    write_events(args.db_path, records)

    print(f"Fetched {len(records)} unique events.")
    by_source: dict[str, int] = {}
    for r in records:
        by_source[r.source or "unknown"] = by_source.get(r.source or "unknown", 0) + 1
    for source, count in sorted(by_source.items()):
        print(f"  {source}: {count}")
    print(f"\nRequest outcomes: {status_counts(log)}")
    print(f"Written to {args.db_path} (table ra_events) — gitignored, never committed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
