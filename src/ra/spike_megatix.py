"""Go/no-go feasibility spike for scraping Megatix (megatix.com.au) for
Melbourne rave events from promoters whose own sites don't work directly:
No Sleep Entertainment (nosleepent.com.au is a client-rendered Shopify
page with no usable content) and Dangerous Goods Entertainment (their own
ticket domain, tickets.dangerousgoodsent.com.au, is Oztix white-labelled
under the hood — same client-rendered dead end as Oztix itself, confirmed
by its TLS cert matching *.oztix.com.au). Megatix is where both actually
sell tickets.

Like Ticketbooth and Ticket Merchant, Megatix's `/events` browse page is
itself a Nuxt.js single-page app (`_nuxt/BrowseEvents...` bundle, no
server-rendered listing) — not crawlable. Individual event pages
(`/events/<slug>`) are server-rendered with real JSON-LD though, so this
spike seeds from known event URLs rather than a search endpoint.

Identifies honestly with a descriptive contact user agent (not a browser
spoof, not a bare bot name) and checks robots.txt before every request.
Run: uv run python -m src.ra.spike_megatix --output docs/megatix-feasibility.md
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

BASE_URL = "https://megatix.com.au"
USER_AGENT = (
    "rave-economics-research/0.1 "
    "(Australia DS honours project; contact: michaelvallen14@gmail.com)"
)
REQUEST_DELAY_SECONDS = 1.5
TIMEOUT_SECONDS = 20

# Seed URLs: promoter -> event, found via web search, not platform
# discovery (see module docstring) — Megatix's own browse page is
# client-rendered.
SEED_EVENTS = [
    ("No Sleep Entertainment", f"{BASE_URL}/events/the-uprising"),
    (
        "No Sleep Entertainment",
        f"{BASE_URL}/events/rave-arcade-no-sleep-entertainment-4th-birthday",
    ),
    ("Dangerous Goods Entertainment", f"{BASE_URL}/events/dangerous-goods-6-xxl-early-access-save-130"),
]


def parse_event(html_text: str, url: str) -> EventRecord:
    event = find_event_jsonld(html_text)
    if event is None:
        return EventRecord(url=url)
    return parse_event_from_jsonld(event, url)


def fetch_events(client: httpx.Client, log: list[FetchLog]) -> list[EventRecord]:
    records = []
    for promoter, url in SEED_EVENTS:
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
            record = parse_event(response.text, url)
            if record.promoter is None:
                record.promoter = promoter
            records.append(record)
        time.sleep(REQUEST_DELAY_SECONDS)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="docs/megatix-feasibility.md")
    args = parser.parse_args()

    log: list[FetchLog] = []
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(headers=headers, timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
        records = fetch_events(client, log)

    sample_size = len(SEED_EVENTS)
    report = render_report(
        title="Megatix feasibility spike",
        access_notes=[
            "No Sleep Entertainment's own site (nosleepent.com.au) is a "
            "dead end — its `/pages/events` page is a nearly-empty Shopify "
            "template with no static event content; the real listing is "
            "injected client-side. Dangerous Goods Entertainment's own "
            "ticket domain (tickets.dangerousgoodsent.com.au) is a dead end "
            "too — its TLS cert matches `*.oztix.com.au`, meaning it's "
            "Oztix white-labelled under a custom domain, same "
            "client-rendered problem as Oztix itself. Megatix "
            "(megatix.com.au) is where both actually sell tickets, found "
            "via web search, not the promoter sites.",
            "Megatix's own `/events` browse page is itself a Nuxt.js SPA "
            "(`_nuxt/BrowseEvents...` bundle referenced, no server-rendered "
            "listing) — not crawlable, same problem as Oztix/AREP. "
            "Individual event pages (`/events/<slug>`) are server-rendered "
            "with real JSON-LD though, so this spike seeds from three known "
            "event URLs (two promoters) rather than a search endpoint.",
            "`robots.txt` has no AI-crawler disallow.",
            "No bot-management challenge observed — plain HTTP 200s on "
            "all seed event pages.",
            "Each event page embeds one `schema.org` `Event` JSON-LD block "
            "with `name`, `startDate`, `offers.price`, and "
            "`location.name`/`address`. `promoter` is not in the JSON-LD "
            "and is filled in from the seed list's own promoter label "
            "rather than scraped.",
            "`genre_tags` and `attendance_indicator` are not present in "
            "the JSON-LD and are not scraped from anywhere else — left "
            "unpopulated rather than guessed.",
        ],
        intended_sample_size=sample_size,
        urls_found=sample_size,
        records=records,
        log=log,
        go_note=(
            "Price viable — Megatix closes the gap left by No Sleep "
            "Entertainment's and Dangerous Goods' own unusable sites. Same "
            "discovery caveat as Ticketbooth/Ticket Merchant: needs a "
            "maintained seed list, not a crawlable index."
        ),
        nogo_note=(
            "Price not viable on this seed set — re-check whether these "
            "specific events are still listed or whether Megatix's JSON-LD "
            "shape changed."
        ),
    )
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
