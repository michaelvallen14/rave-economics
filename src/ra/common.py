"""Shared plumbing for the Part A ticketing-platform feasibility spikes
(spike.py, spike_moshtix.py, spike_ticketbooth.py, spike_ticketmerchant.py).

Every spike probes a different site but follows the same shape: check
robots.txt, fetch pages with an honest contact user agent, parse whatever
schema.org Event/MusicEvent JSON-LD is on the page, and report field
completeness against a price-completeness go/no-go threshold.
"""

from __future__ import annotations

import html
import json
import re
import urllib.robotparser
from dataclasses import dataclass, fields
from datetime import datetime, timezone

import httpx

GO_THRESHOLD_PCT = 50
JSON_LD_RE = re.compile(
    r'<script type="application/ld\+json"[^>]*>\s*(.*?)\s*</script>', re.DOTALL
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


def robots_allowed(client: httpx.Client, base_url: str, url: str, user_agent: str) -> bool:
    response = client.get(f"{base_url}/robots.txt")
    response.raise_for_status()
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(response.text.splitlines())
    return parser.can_fetch(user_agent, url)


def find_all_event_jsonld(html_text: str) -> list[dict]:
    """Return every schema.org Event/MusicEvent JSON-LD block on the page —
    some listing pages (e.g. a tour's landing page) embed one block per
    date rather than one block per page."""
    events = []
    for block in JSON_LD_RE.findall(html_text):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        candidates = data if isinstance(data, list) else [data]
        for candidate in candidates:
            if isinstance(candidate, dict) and str(candidate.get("@type", "")).endswith("Event"):
                events.append(candidate)
    return events


def find_event_jsonld(html_text: str) -> dict | None:
    """Return the first schema.org Event/MusicEvent JSON-LD block on the
    page, whether it's a bare object or wrapped in a list."""
    events = find_all_event_jsonld(html_text)
    return events[0] if events else None


def unescape(value: str | None) -> str | None:
    return html.unescape(value) if value else None


def parse_event_from_jsonld(event: dict, url: str) -> EventRecord:
    location = event.get("location") or {}
    offers = event.get("offers") or []
    if isinstance(offers, dict):
        offers = [offers]
    performers = event.get("performers") or event.get("performer") or []
    if isinstance(performers, dict):
        performers = [performers]
    elif isinstance(performers, str):
        performers = [{"name": performers}]

    prices = [o["price"] for o in offers if isinstance(o, dict) and o.get("price")]
    performer_names = [p["name"] for p in performers if isinstance(p, dict) and p.get("name")]

    organizer = event.get("organizer") or {}

    return EventRecord(
        url=url,
        date=unescape(event.get("startDate")),
        name=unescape(event.get("name")),
        venue=unescape(location.get("name")),
        lineup=unescape(", ".join(performer_names)) if performer_names else None,
        promoter=unescape(organizer.get("name")) if isinstance(organizer, dict) else None,
        genre_tags=None,
        price=unescape(min(prices, key=float)) if prices else None,
        attendance_indicator=None,
    )


def completeness_table(records: list[EventRecord], intended_sample_size: int) -> dict[str, float]:
    denominator = max(intended_sample_size, 1)
    return {
        field: round(100 * sum(1 for r in records if getattr(r, field)) / denominator, 1)
        for field in FIELD_NAMES
    }


def status_counts(log: list[FetchLog]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in log:
        key = str(entry.status_code) if entry.status_code else (entry.error or "unknown error")
        counts[key] = counts.get(key, 0) + 1
    return counts


def render_report(
    title: str,
    access_notes: list[str],
    intended_sample_size: int,
    urls_found: int,
    records: list[EventRecord],
    log: list[FetchLog],
    go_note: str,
    nogo_note: str,
) -> str:
    table = completeness_table(records, intended_sample_size)
    price_pct = table["price"]
    decision = "GO" if price_pct >= GO_THRESHOLD_PCT else "NO-GO"

    lines = [
        f"# {title}",
        "",
        f"Run: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Target sample size: {intended_sample_size} events",
        f"Event URLs discovered: {urls_found}",
        f"Events successfully fetched and parsed: {len(records)}",
        "",
        "## Access notes",
        "",
    ]
    lines += [f"- {note}" for note in access_notes]
    lines += [
        "",
        "## Request outcomes",
        "",
        "| Outcome | Count |",
        "|---|---|",
    ]
    for key, count in sorted(status_counts(log).items()):
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
        f"Threshold is {GO_THRESHOLD_PCT}%. Result: **{decision}**.",
        "",
    ]
    if not records:
        lines.append(
            f"No events were fetched at all (0/{intended_sample_size}) — the "
            "acquisition layer itself is blocked, so no field is assessable, "
            "not just price."
        )
    elif decision == "GO":
        lines.append(go_note)
    else:
        lines.append(nogo_note)
    return "\n".join(lines) + "\n"
