"""Go/no-go feasibility spike for scraping Ticketbooth/Leap Events
(events.ticketbooth.com.au, events.leapevents.com — same platform, two
hostnames) for Australian harder-styles rave events.

Unlike ra.co or Moshtix, this platform has no public browse/search page
(root and `/events` both fail) — `events.ticketbooth.com.au/` and
`events.leapevents.com/` return 403, `/events` returns 404. There is no way
to discover events on the platform itself; every event URL below was found
by reading promoter pages (HSU, Symbiotic) or via web search (MASIF, Ultra
Australia) and following their outbound ticket links. This is a curated
seed list, not a crawl — treat the sample size accordingly.

Identifies honestly with a descriptive contact user agent (not a browser
spoof, not a bare bot name) and checks robots.txt before every request.
Run: uv run python -m src.ra.spike_ticketbooth --output docs/ticketbooth-feasibility.md
"""

from __future__ import annotations

import argparse
import sys
import time

import httpx

from src.ra.common import (
    EventRecord,
    FetchLog,
    find_event_jsonld,
    parse_event_from_jsonld,
    render_report,
    robots_allowed,
)

USER_AGENT = (
    "rave-economics-research/0.1 "
    "(Australia DS honours project; contact: michaelvallen14@gmail.com)"
)
REQUEST_DELAY_SECONDS = 1.5
TIMEOUT_SECONDS = 20

# Seed URLs: promoter -> event, found via promoter pages / web search, not
# platform discovery (see module docstring).
SEED_EVENTS = [
    ("MASIF", "https://events.ticketbooth.com.au/event/masif-presents-audiofreq-2024"),
    ("HSU", "https://events.ticketbooth.com.au/event/knockout-outdoor-2026-level-up"),
    ("Symbiotic", "https://events.ticketbooth.com.au/tickets/transmission-elysium-aus-2024"),
    ("Symbiotic", "https://events.ticketbooth.com.au/tickets/hyperdome-2024"),
    ("Ultra Australia", "https://events.leapevents.com/tickets/ultra-australia-2026"),
]


def base_url_for(url: str) -> str:
    return "/".join(url.split("/")[:3])


def parse_event(html_text: str, url: str) -> EventRecord:
    event = find_event_jsonld(html_text)
    if event is None:
        return EventRecord(url=url)
    return parse_event_from_jsonld(event, url)


def fetch_events(client: httpx.Client, log: list[FetchLog]) -> list[EventRecord]:
    records = []
    for promoter, url in SEED_EVENTS:
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
            record = parse_event(response.text, url)
            if record.promoter is None:
                record.promoter = promoter
            records.append(record)
        time.sleep(REQUEST_DELAY_SECONDS)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="docs/ticketbooth-feasibility.md")
    args = parser.parse_args()

    log: list[FetchLog] = []
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(headers=headers, timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
        records = fetch_events(client, log)

    sample_size = len(SEED_EVENTS)
    report = render_report(
        title="Ticketbooth/Leap Events feasibility spike",
        access_notes=[
            "No public browse/search page: `events.ticketbooth.com.au/` and "
            "`events.leapevents.com/` both return 403 on the bare root, and "
            "`/events` returns 404 on both. Individual event pages "
            "(`/event/<slug>` or `/tickets/<slug>`) work fine — there just "
            "isn't an index to crawl.",
            "This spike therefore uses a curated seed list of 5 known events "
            "across 4 promoters (MASIF, HSU, Symbiotic x2, Ultra Australia), "
            "found by reading promoter pages' outbound links or web search — "
            "not discovered from the platform itself. A production version "
            "would need a maintained list of promoter pages to poll, not a "
            "single listing endpoint like Moshtix's search.",
            "`robots.txt` on both hostnames is a standard e-commerce "
            "boilerplate (login/checkout/dashboard paths) with no AI-crawler "
            "disallow.",
            "No bot-management challenge observed — plain HTTP 200s on every "
            "event page tried.",
            "Each event page embeds one `schema.org` `Event` JSON-LD block "
            "with `name`, `startDate`, `offers[].price`, and "
            "`location.name`/`address`. `promoter` is filled from the "
            "JSON-LD `organizer.name` where present, falling back to the "
            "promoter name from the seed list.",
            "`genre_tags` and `attendance_indicator` are not present in the "
            "JSON-LD and are not scraped from anywhere else — left "
            "unpopulated rather than guessed.",
        ],
        intended_sample_size=sample_size,
        urls_found=sample_size,
        records=records,
        log=log,
        go_note=(
            "Price viable across MASIF, HSU, Symbiotic and Ultra Australia — "
            "Ticketbooth/Leap Events is a genuine multi-promoter source for "
            "the harder-styles/rave segment, not just one brand. Discovery "
            "is the open problem, not access: this platform needs a "
            "maintained list of promoter pages to poll rather than a single "
            "crawlable listing."
        ),
        nogo_note=(
            "Price not viable across this seed set — re-examine whether the "
            "JSON-LD shape has changed or whether these specific events are "
            "no longer on sale."
        ),
    )
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
