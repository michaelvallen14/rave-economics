"""Recompute genre_tags for events already sitting in the local DuckDB
table, using the current genre.py classifier — needed once, whenever the
keyword/artist lists in genre.py change, since scrape.py only classifies
on acquisition, not read.

Run: uv run python -m src.ra.reclassify_genre
"""

from __future__ import annotations

import argparse
import sys

import duckdb

from src.ra.genre import classify_genre
from src.ra.scrape import DEFAULT_DB_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    con = duckdb.connect(args.db_path)
    try:
        rows = con.execute("SELECT url, name, lineup FROM ra_events").fetchall()
        updates = [
            (classify_genre(name, lineup), url) for url, name, lineup in rows
        ]
        con.executemany(
            "UPDATE ra_events SET genre_tags = ? WHERE url = ?", updates
        )
        matched = sum(1 for genre_tags, _ in updates if genre_tags)
    finally:
        con.close()

    print(f"Reclassified {len(updates)} events; {matched} tagged as harder styles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
