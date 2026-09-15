"""Go/no-go feasibility spike for scraping Ticket Merchant
(theticketmerchant.com.au) for Australian harder-styles rave events.

Ticket Merchant has no dance/electronic category page (it's a general
sports/comedy/concert marketplace), so — like Ticketbooth — this spike
seeds from a small list of known artist/tour landing pages rather than
crawling a genre listing. Unlike Ticketbooth, one landing page (e.g.
`/concert-tickets/teletech-tickets`) embeds a separate `MusicEvent`
JSON-LD block per tour date, so a handful of seed pages still yields a
useful sample.

Note: Ticket Merchant's own JSON-LD marks its offers `"category":
"Secondary"` — this looks like a resale/secondary marketplace, not a
primary box office, so its prices may sit above face value. Relevant if
Part A ever does price/inflation analysis on this source.

Identifies honestly with a descriptive contact user agent (not a browser
spoof, not a bare bot name) and checks robots.txt before every request.
Run: uv run python -m src.ra.spike_ticketmerchant --output docs/ticketmerchant-feasibility.md
"""

from __future__ import annotations

import argparse
import sys
import time

import httpx

from src.ra.common import (
    EventRecord,
    FetchLog,
    find_all_event_jsonld,
    parse_event_from_jsonld,
    render_report,
    robots_allowed,
)

BASE_URL = "https://www.theticketmerchant.com.au"
USER_AGENT = (
    "rave-economics-research/0.1 "
    "(Australia DS honours project; contact: michaelvallen14@gmail.com)"
)
REQUEST_DELAY_SECONDS = 1.5
TIMEOUT_SECONDS = 20

# Seed landing pages: each embeds one JSON-LD MusicEvent block per tour
# date, not just one event (see module docstring).
SEED_PAGES = [
    f"{BASE_URL}/concert-tickets/teletech-tickets",
]


def fetch_events(client: httpx.Client, urls_found: list[str], log: list[FetchLog]) -> list[EventRecord]:
    records = []
    for url in SEED_PAGES:
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
            events = find_all_event_jsonld(response.text)
            for event in events:
                urls_found.append(event.get("url") or url)
                records.append(parse_event_from_jsonld(event, event.get("url") or url))
        time.sleep(REQUEST_DELAY_SECONDS)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="docs/ticketmerchant-feasibility.md")
    args = parser.parse_args()

    log: list[FetchLog] = []
    urls_found: list[str] = []
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(headers=headers, timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
        records = fetch_events(client, urls_found, log)

    sample_size = max(len(urls_found), 1)
    report = render_report(
        title="Ticket Merchant feasibility spike",
        access_notes=[
            "No dance/electronic category page exists — this is a general "
            "sports/comedy/theatre/concert marketplace, not a genre-tagged "
            "listing site. This spike seeds from one known artist landing "
            "page (Teletech) rather than crawling a category.",
            "That one landing page embeds a separate `MusicEvent` JSON-LD "
            "block per tour date, so a handful of seed pages can still "
            "yield a reasonable sample without needing per-event URLs.",
            "`robots.txt` blocks standard account/checkout/admin paths only "
            "— no AI-crawler disallow.",
            "No bot-management challenge observed — plain HTTP 200 on the "
            "seed page.",
            "**Caveat**: offers are marked `\"category\": \"Secondary\"` in "
            "the JSON-LD — this reads as a resale/secondary marketplace, not "
            "a primary box office. Prices here may run above face value, "
            "which matters if this source ever feeds price/inflation "
            "analysis rather than just volume/venue/lineup.",
            "`genre_tags` and `attendance_indicator` are not present in the "
            "JSON-LD and are not scraped from anywhere else — left "
            "unpopulated rather than guessed.",
        ],
        intended_sample_size=sample_size,
        urls_found=len(urls_found),
        records=records,
        log=log,
        go_note=(
            "Price viable — Ticket Merchant works as a source for touring "
            "hard-dance/hardstyle acts (confirmed via Teletech), with the "
            "secondary-market price caveat noted above. Scaling this up "
            "means maintaining a list of artist/tour slugs to seed, same as "
            "Ticketbooth."
        ),
        nogo_note=(
            "Price not viable on this seed page — re-check whether "
            "Teletech's tour is still listed or whether the JSON-LD shape "
            "changed."
        ),
    )
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
