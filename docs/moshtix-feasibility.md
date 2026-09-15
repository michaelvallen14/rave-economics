# Moshtix feasibility spike

Run: 2026-09-15T05:49:43+00:00
Target sample size: 50 Melbourne dance/electronic events
Event URLs discovered from listing pages: 50
Events successfully fetched and parsed: 50

## Access notes

- `robots.txt` (`User-agent: *`) only disallows image extensions (`*.gif`, `*.jpg`, `*.jpeg`, `*.png`) — no AI crawlers, no disallow on `/v2/search` or `/v2/event`.
- No bot-management challenge observed: this script's honest, contact-bearing user agent gets plain HTTP 200s from both the search listing and individual event pages, unlike ra.co's DataDome 403.
- Listing pagination (`&Page=N`) must carry the `location`/`category` query params forward manually — the site's own pagination links drop them (JS-driven on a real browser), but combining params by hand returns distinct pages of results, confirmed against page 1 vs 2.
- Each event page embeds one or more `schema.org` `MusicEvent` JSON-LD blocks; this script parses the first one (the page's own event, not the 'Other Events' recommendations further down) as JSON rather than regex-scraping fields, since it's well-formed structured data.
- `promoter`, `genre_tags`, and `attendance_indicator` are not present in the JSON-LD and are not scraped from anywhere else on the page — left unpopulated rather than guessed.

## Request outcomes

| Outcome | Count |
|---|---|
| 200 | 53 |

## Field completeness

Percentage of the intended sample (denominator = target sample size, not just successfully fetched events) with each field populated.

| Field | Populated |
|---|---|
| date | 100.0% |
| name | 100.0% |
| venue | 100.0% |
| lineup | 56.0% |
| promoter | 0.0% |
| genre_tags | 0.0% |
| price | 64.0% |
| attendance_indicator | 0.0% |

## Decision

Ticket price populated for **64.0%** of the target sample.
Threshold is 50%. Result: **GO**.

Price viable — Moshtix is a workable ra.co replacement for Part A's acquisition layer. `lineup`/`promoter`/`genre_tags` gaps mean the artist-network and genre-tagging analysis will need a secondary source or manual coding on top of this.
