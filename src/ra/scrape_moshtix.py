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

IMPORTANT (found 2026-09-22): Moshtix's `category=Dance%2FElectronic`
query parameter does nothing — verified by requesting the same search
with and without it, with and without `location=`, and getting byte-
identical results every time (page 1 includes things like a thrift-store
market and a racing-club membership). The server ignores it entirely; it
isn't a plain-HTTP client problem to work around, there's just no
server-side category filter to rely on. So this crawls Moshtix's general
listing (which spans every category, not just Dance/Electronic) and
applies its own client-side filter — DANCE_ELECTRONIC_TERMS matched
against each event's URL slug — before spending a request on the full
event page. That filter is precision-first like genre.py's harder-styles
one: matches on real, distinctive genre/scene words, so it undercounts
(an event with no genre word in its slug, e.g. an artist name alone,
gets skipped) rather than readmitting the ~93% of the raw listing that
isn't dance/electronic at all.

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
# Bumped from 40: the listing's real category filter is broken (see
# module docstring), so a much deeper crawl of the unfiltered listing is
# needed to find `limit` events that pass the client-side genre filter.
MAX_PAGES = 250
EVENT_LINK_RE = re.compile(
    r'href="(https://www\.moshtix\.com\.au/v2/event/([a-z0-9\-]+)/\d+)"'
)

# Client-side stand-in for Moshtix's non-functional category filter,
# matched against each event's URL slug (hyphens treated as spaces).
# Precision-first: real dance/electronic terms only, not generic words
# like "party" or "festival" that would readmit unrelated events.
DANCE_ELECTRONIC_TERMS = [
    "house", "techno", "edm", "dnb", "drum and bass", "bass", "trance",
    "dubstep", "electro", "rave", "disco", "garage", "hardstyle",
    "hardcore", "psytrance", "deep house", "tech house", "b2b",
    "allstars", "club night", "dance party", "dance music", "dj",
]
_SLUG_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in DANCE_ELECTRONIC_TERMS) + r")\b",
    re.IGNORECASE,
)


def is_dance_electronic_slug(slug: str) -> bool:
    return bool(_SLUG_PATTERN.search(slug.replace("-", " ")))


def fetch_listing_urls(client: httpx.Client, limit: int, log: list[FetchLog]) -> list[str]:
    urls: list[str] = []
    seen_slugs: set[str] = set()
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

        pairs = dict.fromkeys(EVENT_LINK_RE.findall(response.text))
        new_slugs = [(u, s) for u, s in pairs if s not in seen_slugs]
        if not new_slugs:
            break
        for url, slug in new_slugs:
            seen_slugs.add(slug)
            if is_dance_electronic_slug(slug):
                urls.append(url)
        page += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    return urls[:limit]


def parse_event(html_text: str, url: str) -> EventRecord:
    event = find_event_jsonld(html_text)
    if event is None:
        return EventRecord(url=url, source="moshtix")
    return parse_event_from_jsonld(event, url, source="moshtix")


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
