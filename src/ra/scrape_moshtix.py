"""Real (non-spike) scraper for Moshtix (moshtix.com.au) dance/electronic
events, Australia-wide — not Melbourne-only, per the project's Part A
scope. See docs/moshtix-feasibility.md for the feasibility result this
replaces (64% price completeness, GO).

Unlike spike_moshtix.py, this drops the `location=melbourne` search
parameter entirely rather than trying to fix its loose geo-filtering:
easier to capture every event's real city/region from its own JSON-LD
address fields (now on EventRecord) than to trust the search UI's
location matching, which the spike showed pulls in interstate results
anyway.

Used by src/ra/scrape.py; not meant to be run standalone, but has a
__main__ guard for quick manual checks per CLAUDE.md's working
conventions.
"""

from __future__ import annotations

import argparse
import re
import sys
import time

import httpx

from src.ra.common import EventRecord, FetchLog, find_event_jsonld, parse_event_from_jsonld, robots_allowed

BASE_URL = "https://www.moshtix.com.au"
SEARCH_URL = f"{BASE_URL}/v2/search?category=Dance%2FElectronic"
USER_AGENT = (
    "rave-economics-research/0.1 "
    "(Australia DS honours project; contact: michaelvallen14@gmail.com)"
)
REQUEST_DELAY_SECONDS = 1.5
TIMEOUT_SECONDS = 20
MAX_PAGES = 40
EVENT_LINK_RE = re.compile(
    r'href="(https://www\.moshtix\.com\.au/v2/event/[a-z0-9\-]+/\d+)"'
)


def fetch_listing_urls(client: httpx.Client, limit: int, log: list[FetchLog]) -> list[str]:
    urls: list[str] = []
    page = 1
    while len(urls) < limit and page <= MAX_PAGES:
        page_url = f"{SEARCH_URL}&Page={page}"
        if not robots_allowed(client, BASE_URL, page_url, USER_AGENT):
            log.append(FetchLog(page_url, None, "disallowed by robots.txt"))
            break

        try:
            response = client.get(page_url)
        except httpx.HTTPError as exc:
            log.append(FetchLog(page_url, None, str(exc)))
            break

        log.append(FetchLog(page_url, response.status_code))
        if response.status_code != 200:
            break

        hrefs = EVENT_LINK_RE.findall(response.text)
        new_urls = [u for u in dict.fromkeys(hrefs) if u not in urls]
        if not new_urls:
            break
        urls.extend(new_urls)
        page += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    return urls[:limit]


def parse_event(html_text: str, url: str) -> EventRecord:
    event = find_event_jsonld(html_text)
    if event is None:
        return EventRecord(url=url, source="moshtix")
    record = parse_event_from_jsonld(event, url, source="moshtix")
    record.genre_tags = "Dance/Electronic"
    return record


def fetch_events(client: httpx.Client, limit: int, log: list[FetchLog]) -> list[EventRecord]:
    urls = fetch_listing_urls(client, limit, log)
    records = []
    for url in urls:
        if not robots_allowed(client, BASE_URL, url, USER_AGENT):
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
            records.append(parse_event(response.text, url))
        time.sleep(REQUEST_DELAY_SECONDS)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    log: list[FetchLog] = []
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(headers=headers, timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
        records = fetch_events(client, args.limit, log)

    for record in records:
        print(record)
    print(f"\n{len(records)} events fetched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
