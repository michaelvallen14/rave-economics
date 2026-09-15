"""Go/no-go feasibility spike for scraping Resident Advisor (ra.co) event
listings for Melbourne.

Probe only. Fetches roughly `--limit` past Melbourne events, records which
fields are populated, and writes a field-completeness report. See
docs/ra-feasibility.md for the result of the last run.

Identifies honestly with a descriptive contact user agent (not a browser
spoof, not a bare bot name) and checks robots.txt before every request.
Run: uv run python -m src.ra.spike --limit 50 --output docs/ra-feasibility.md
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.robotparser
from dataclasses import dataclass, fields
from datetime import datetime, timezone

import httpx

BASE_URL = "https://ra.co"
LISTING_URL = f"{BASE_URL}/events/au/melbourne"
USER_AGENT = (
    "rave-economics-research/0.1 "
    "(Melbourne DS honours project; contact: michaelvallen14@gmail.com)"
)
REQUEST_DELAY_SECONDS = 1.5
TIMEOUT_SECONDS = 20


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
    """Check robots.txt, fetched with our own UA (robotparser.read() uses
    urllib's default UA, which ra.co's bot-management 403s independently
    of what the real robots.txt says)."""
    response = client.get(f"{BASE_URL}/robots.txt")
    response.raise_for_status()
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(response.text.splitlines())
    return parser.can_fetch(user_agent, url)


def fetch_listing_urls(client: httpx.Client, limit: int, log: list[FetchLog]) -> list[str]:
    if not robots_allowed(client, LISTING_URL, USER_AGENT):
        log.append(FetchLog(LISTING_URL, None, "disallowed by robots.txt"))
        return []

    try:
        response = client.get(LISTING_URL)
    except httpx.HTTPError as exc:
        log.append(FetchLog(LISTING_URL, None, str(exc)))
        return []

    log.append(FetchLog(LISTING_URL, response.status_code))
    if response.status_code != 200:
        return []

    hrefs = re.findall(r'href="(/events/\d+-[a-z0-9\-]+)"', response.text)
    unique = list(dict.fromkeys(hrefs))
    return [f"{BASE_URL}{href}" for href in unique[:limit]]


def parse_event(html: str, url: str) -> EventRecord:
    def find(pattern: str) -> str | None:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None

    return EventRecord(
        url=url,
        date=find(r'"date"\s*:\s*"([^"]+)"'),
        name=find(r'"name"\s*:\s*"([^"]+)"'),
        venue=find(r'"venue"\s*:\s*\{[^}]*"name"\s*:\s*"([^"]+)"'),
        lineup=find(r'"lineup"\s*:\s*"([^"]+)"'),
        promoter=find(r'"promoter"\s*:\s*\{[^}]*"name"\s*:\s*"([^"]+)"'),
        genre_tags=find(r'"genre"\s*:\s*"([^"]+)"'),
        price=find(r'"price"\s*:\s*"([^"]+)"'),
        attendance_indicator=find(r'"attending"\s*:\s*"?(\d+)"?'),
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
        "# RA feasibility spike",
        "",
        f"Run: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Target sample size: {intended_sample_size} Melbourne events",
        f"Event URLs discovered from listing page: {urls_found}",
        f"Events successfully fetched and parsed: {len(records)}",
        "",
        "## Access notes",
        "",
        "- `robots.txt` (`User-agent: *`) permits `/events/...` — it only blocks "
        "`/pro`, `/user`, `/api`, `/my-tickets`, `/logout.aspx`, `/inbox.aspx`, `/widget`.",
        "- `robots.txt` separately, explicitly disallows `ClaudeBot` and `anthropic-ai` "
        "from the entire site (`Disallow: /`), alongside GPTBot, CCBot, PerplexityBot "
        "and other AI crawlers. This script identifies as a distinct, descriptive, "
        "contact-bearing UA (not those tokens, not a browser spoof) and only requests "
        "paths `robots.txt` permits for `*`.",
        "- Independent of robots.txt: ra.co sits behind DataDome bot-management. A "
        "plain HTTP GET to the listing page returns HTTP 403 with a JS/CAPTCHA "
        "challenge page, reproduced identically with both this script's UA and a "
        "full desktop Chrome UA string — this is fingerprint/behaviour-based "
        "blocking, not a UA string check.",
        "- This spike does not attempt to solve the challenge or automate a real "
        "browser session to get past it — that would mean building anti-bot-detection "
        "evasion tooling against a site whose robots.txt already names AI crawlers as "
        "unwelcome, which is out of scope for this project.",
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
            "No events were fetched at all (0/{0}) — this is a harder failure than "
            "a missing-price case. The acquisition layer itself is blocked, so no "
            "field is assessable, not just price. Live scraping of ra.co via a "
            "polite HTTP client is not viable in its current form.".format(intended_sample_size)
        )
    elif decision == "GO":
        lines.append("Price viable — Part A's inflation analysis can proceed.")
    else:
        lines.append(
            "Price not viable — Part A should be rebuilt around volume, "
            "venue concentration and the artist/promoter network only."
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--output", default="docs/ra-feasibility.md")
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
