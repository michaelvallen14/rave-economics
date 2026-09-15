# Megatix feasibility spike

Run: 2026-09-15T08:03:00+00:00
Target sample size: 2 events
Event URLs discovered: 2
Events successfully fetched and parsed: 2

## Access notes

- No Sleep Entertainment's own site (nosleepent.com.au) is a dead end — its `/pages/events` page is a nearly-empty Shopify template with no static event content; the real listing is injected client-side. Megatix (megatix.com.au) is where they actually sell tickets, found via web search, not the promoter site.
- Megatix's own `/events` browse page is itself a Nuxt.js SPA (`_nuxt/BrowseEvents...` bundle referenced, no server-rendered listing) — not crawlable, same problem as Oztix/AREP. Individual event pages (`/events/<slug>`) are server-rendered with real JSON-LD though, so this spike seeds from two known event URLs rather than a search endpoint.
- `robots.txt` has no AI-crawler disallow.
- No bot-management challenge observed — plain HTTP 200s on both seed event pages.
- Each event page embeds one `schema.org` `Event` JSON-LD block with `name`, `startDate`, `offers.price`, and `location.name`/`address`. `promoter` is not in the JSON-LD and is filled in from context (this is a No Sleep Entertainment-specific seed list) rather than scraped.
- `genre_tags` and `attendance_indicator` are not present in the JSON-LD and are not scraped from anywhere else — left unpopulated rather than guessed.

## Request outcomes

| Outcome | Count |
|---|---|
| 200 | 2 |

## Field completeness

Percentage of the intended sample (denominator = target sample size, not just successfully fetched events) with each field populated.

| Field | Populated |
|---|---|
| date | 100.0% |
| name | 100.0% |
| venue | 100.0% |
| lineup | 0.0% |
| promoter | 100.0% |
| genre_tags | 0.0% |
| price | 100.0% |
| attendance_indicator | 0.0% |

## Decision

Ticket price populated for **100.0%** of the target sample.
Threshold is 50%. Result: **GO**.

Price viable — Megatix closes the No Sleep Entertainment gap left by their own unusable site. Same discovery caveat as Ticketbooth/Ticket Merchant: needs a maintained seed list, not a crawlable index.
