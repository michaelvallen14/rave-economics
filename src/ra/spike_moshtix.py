"""Go/no-go feasibility spike for scraping Moshtix (moshtix.com.au) event
listings for Melbourne, evaluated as a fallback acquisition source after the
ra.co spike (see docs/ra-feasibility.md) came back NO-GO on access grounds.

Probe only. Fetches roughly `--limit` Melbourne dance/electronic events,
records which fields are populated from each event's schema.org JSON-LD
block, and writes a field-completeness report.

Identifies honestly with a descriptive contact user agent (not a browser
spoof, not a bare bot name) and checks robots.txt before every request.
Run: uv run python -m src.ra.spike_moshtix --limit 50 --output docs/moshtix-feasibility.md
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.robotparser
from dataclasses import dataclass, fields
from datetime import datetime, timezone

import httpx

BASE_URL = "https://www.moshtix.com.au"
SEARCH_URL = f"{BASE_URL}/v2/search?location=melbourne&category=Dance%2FElectronic"
USER_AGENT = (
    "rave-economics-research/0.1 "
    "(Melbourne DS honours project; contact: michaelvallen14@gmail.com)"
)
REQUEST_DELAY_SECONDS = 1.5
TIMEOUT_SECONDS = 20
EVENT_LINK_RE = re.compile(
    r'href="(https://www\.moshtix\.com\.au/v2/event/[a-z0-9\-]+/\d+)"'
)


@dataclass
class EventRecord:
    url: str
    date: str | None = None
    name: str | None = None
    venue: str | None = None
    lineup: str | None = None
    promoter: str | None = None
    genre_tags: str | None = None
    price: str | None = None
    attendance_indicator: str | None = None


FIELD_NAMES = [f.name for f in fields(EventRecord) if f.name != "url"]


@dataclass
class FetchLog:
    url: str
    status_code: int | None
    error: str | None = None


def robots_allowed(client: httpx.Client, url: str, user_agent: str) -> bool:
    response = client.get(f"{BASE_URL}/robots.txt")
    response.raise_for_status()
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(response.text.splitlines())
    return parser.can_fetch(user_agent, url)


def fetch_listing_urls(client: httpx.Client, limit: int, log: list[FetchLog]) -> list[str]:
    urls: list[str] = []
    page = 1
    while len(urls) < limit:
        page_url = f"{SEARCH_URL}&Page={page}"
        if not robots_allowed(client, page_url, USER_AGENT):
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
    match = re.search(
        r'<script type="application/ld\+json">\s*(\[.*?\])\s*</script>',
        html_text,
        re.DOTALL,
    )
    if not match:
        return EventRecord(url=url)

    try:
        data = json.loads(match.group(1))
        event = data[0] if data else {}
    except (json.JSONDecodeError, IndexError):
        return EventRecord(url=url)

    def unescape(value: str | None) -> str | None:
        return html.unescape(value) if value else None

    location = event.get("location") or {}
    offers = event.get("offers") or []
    performers = event.get("performers") or []

    prices = [o["price"] for o in offers if o.get("price")]
    performer_names = [p["name"] for p in performers if p.get("name")]

    return EventRecord(
        url=url,
        date=unescape(event.get("startDate")),
        name=unescape(event.get("name")),
        venue=unescape(location.get("name")),
        lineup=unescape(", ".join(performer_names)) if performer_names else None,
        promoter=None,
        genre_tags=None,
        price=unescape(min(prices, key=float)) if prices else None,
        attendance_indicator=None,
    )


def fetch_events(client: httpx.Client, urls: list[str], log: list[FetchLog]) -> list[EventRecord]:
    records = []
    for url in urls:
        if not robots_allowed(client, url, USER_AGENT):
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


def completeness_table(records: list[EventRecord], intended_sample_size: int) -> dict[str, float]:
    denominator = max(intended_sample_size, 1)
    return {
        field: round(100 * sum(1 for r in records if getattr(r, field)) / denominator, 1)
        for field in FIELD_NAMES
    }


def render_report(
    intended_sample_size: int,
    urls_found: int,
    records: list[EventRecord],
    log: list[FetchLog],
) -> str:
    table = completeness_table(records, intended_sample_size)
    price_pct = table["price"]
    decision = "GO" if price_pct >= 50 else "NO-GO"

    status_counts: dict[str, int] = {}
    for entry in log:
        key = str(entry.status_code) if entry.status_code else (entry.error or "unknown error")
        status_counts[key] = status_counts.get(key, 0) + 1

    lines = [
        "# Moshtix feasibility spike",
        "",
        f"Run: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Target sample size: {intended_sample_size} Melbourne dance/electronic events",
        f"Event URLs discovered from listing pages: {urls_found}",
        f"Events successfully fetched and parsed: {len(records)}",
        "",
        "## Access notes",
        "",
        "- `robots.txt` (`User-agent: *`) only disallows image extensions "
        "(`*.gif`, `*.jpg`, `*.jpeg`, `*.png`) — no AI crawlers, no disallow on "
        "`/v2/search` or `/v2/event`.",
        "- No bot-management challenge observed: this script's honest, "
        "contact-bearing user agent gets plain HTTP 200s from both the search "
        "listing and individual event pages, unlike ra.co's DataDome 403.",
        "- Listing pagination (`&Page=N`) must carry the `location`/`category` "
        "query params forward manually — the site's own pagination links drop "
        "them (JS-driven on a real browser), but combining params by hand "
        "returns distinct pages of results, confirmed against page 1 vs 2.",
        "- Each event page embeds one or more `schema.org` `MusicEvent` "
        "JSON-LD blocks; this script parses the first one (the page's own "
        "event, not the 'Other Events' recommendations further down) as JSON "
        "rather than regex-scraping fields, since it's well-formed structured "
        "data.",
        "- `promoter`, `genre_tags`, and `attendance_indicator` are not present "
        "in the JSON-LD and are not scraped from anywhere else on the page — "
        "left unpopulated rather than guessed.",
        "",
        "## Request outcomes",
        "",
        "| Outcome | Count |",
        "|---|---|",
    ]
    for key, count in sorted(status_counts.items()):
        lines.append(f"| {key} | {count} |")

    lines += [
        "",
        "## Field completeness",
        "",
        "Percentage of the intended sample (denominator = target sample size, "
        "not just successfully fetched events) with each field populated.",
        "",
        "| Field | Populated |",
        "|---|---|",
    ]
    for field, pct in table.items():
        lines.append(f"| {field} | {pct}% |")

    lines += [
        "",
        "## Decision",
        "",
        f"Ticket price populated for **{price_pct}%** of the target sample.",
        f"Threshold is 50%. Result: **{decision}**.",
        "",
    ]
    if not records:
        lines.append(
            "No events were fetched at all (0/{0}) — the acquisition layer "
            "itself is blocked, so no field is assessable, not just "
            "price.".format(intended_sample_size)
        )
    elif decision == "GO":
        lines.append(
            "Price viable — Moshtix is a workable ra.co replacement for Part A's "
            "acquisition layer. `lineup`/`promoter`/`genre_tags` gaps mean the "
            "artist-network and genre-tagging analysis will need a secondary "
            "source or manual coding on top of this."
        )
    else:
        lines.append(
            "Price not viable — Part A should be rebuilt around volume and "
            "venue concentration only, or another source evaluated."
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--output", default="docs/moshtix-feasibility.md")
    args = parser.parse_args()

    log: list[FetchLog] = []
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(headers=headers, timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
        urls = fetch_listing_urls(client, args.limit, log)
        records = fetch_events(client, urls, log) if urls else []

    report = render_report(args.limit, len(urls), records, log)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
