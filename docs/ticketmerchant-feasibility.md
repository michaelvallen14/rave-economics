# Ticket Merchant feasibility spike

Run: 2026-09-15T07:29:32+00:00
Target sample size: 3 events
Event URLs discovered: 3
Events successfully fetched and parsed: 3

## Access notes

- No dance/electronic category page exists — this is a general sports/comedy/theatre/concert marketplace, not a genre-tagged listing site. This spike seeds from one known artist landing page (Teletech) rather than crawling a category.
- That one landing page embeds a separate `MusicEvent` JSON-LD block per tour date, so a handful of seed pages can still yield a reasonable sample without needing per-event URLs.
- `robots.txt` blocks standard account/checkout/admin paths only — no AI-crawler disallow.
- No bot-management challenge observed — plain HTTP 200 on the seed page.
- **Caveat**: offers are marked `"category": "Secondary"` in the JSON-LD — this reads as a resale/secondary marketplace, not a primary box office. Prices here may run above face value, which matters if this source ever feeds price/inflation analysis rather than just volume/venue/lineup.
- `genre_tags` and `attendance_indicator` are not present in the JSON-LD and are not scraped from anywhere else — left unpopulated rather than guessed.

## Request outcomes

| Outcome | Count |
|---|---|
| 200 | 1 |

## Field completeness

Percentage of the intended sample (denominator = target sample size, not just successfully fetched events) with each field populated.

| Field | Populated |
|---|---|
| date | 100.0% |
| name | 100.0% |
| venue | 100.0% |
| lineup | 100.0% |
| promoter | 100.0% |
| genre_tags | 0.0% |
| price | 100.0% |
| attendance_indicator | 0.0% |

## Decision

Ticket price populated for **100.0%** of the target sample.
Threshold is 50%. Result: **GO**.

Price viable — Ticket Merchant works as a source for touring hard-dance/hardstyle acts (confirmed via Teletech), with the secondary-market price caveat noted above. Scaling this up means maintaining a list of artist/tour slugs to seed, same as Ticketbooth.
