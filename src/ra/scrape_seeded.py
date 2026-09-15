"""Real (non-spike) scraper for the three seeded ticketing platforms:
Ticketbooth/Leap Events, Ticket Merchant, and Megatix. All three have no
crawlable listing page, so discovery comes from the hand-maintained list
in src/ra/seeds.py rather than a search endpoint — see that module's
docstring.

Used by src/ra/scrape.py; not meant to be run standalone, but has a
__main__ guard for quick manual checks per CLAUDE.md's working
conventions.
"""

from __future__ import annotations

import sys
import time

import httpx

from src.ra.common import (
    EventRecord,
    FetchLog,
    find_all_event_jsonld,
    find_event_jsonld,
    parse_event_from_jsonld,
    robots_allowed,
)
from src.ra.seeds import SEEDS

USER_AGENT = (
    "rave-economics-research/0.1 "
    "(Australia DS honours project; contact: michaelvallen14@gmail.com)"
)
REQUEST_DELAY_SECONDS = 1.5
TIMEOUT_SECONDS = 20


def base_url_for(url: str) -> str:
    return "/".join(url.split("/")[:3])


def fetch_seeded_events(client: httpx.Client, log: list[FetchLog]) -> list[EventRecord]:
    records = []
    for platform, promoter, url, multi_event in SEEDS:
        base_url = base_url_for(url)
        if not robots_allowed(client, base_url, url, USER_AGENT):
            log.append(FetchLog(url, None, "disallowed by robots.txt"))
            continue
        try:
            response = client.get(url)
        except httpx.HTTPError as exc:
            log.append(FetchLog(url, None, str(exc)))
            time.sleep(REQUEST_DELAY_SECONDS)
            continue

        log.append(FetchLog(url, response.status_code))
        if response.status_code == 200:
            if multi_event:
                events = find_all_event_jsonld(response.text)
                for event in events:
                    event_url = event.get("url") or url
                    record = parse_event_from_jsonld(event, event_url, source=platform)
                    if record.promoter is None:
                        record.promoter = promoter
                    records.append(record)
            else:
                event = find_event_jsonld(response.text)
                if event is not None:
                    record = parse_event_from_jsonld(event, url, source=platform)
                    if record.promoter is None:
                        record.promoter = promoter
                    records.append(record)
        time.sleep(REQUEST_DELAY_SECONDS)
    return records


def main() -> int:
    log: list[FetchLog] = []
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(headers=headers, timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
        records = fetch_seeded_events(client, log)

    for record in records:
        print(record)
    print(f"\n{len(records)} events fetched from {len(SEEDS)} seed URLs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
