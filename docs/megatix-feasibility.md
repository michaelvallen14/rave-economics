# Megatix feasibility spike

Run: 2026-09-15T08:12:13+00:00
Target sample size: 3 events
Event URLs discovered: 3
Events successfully fetched and parsed: 3

## Access notes

- No Sleep Entertainment's own site (nosleepent.com.au) is a dead end — its `/pages/events` page is a nearly-empty Shopify template with no static event content; the real listing is injected client-side. Dangerous Goods Entertainment's own ticket domain (tickets.dangerousgoodsent.com.au) is a dead end too — its TLS cert matches `*.oztix.com.au`, meaning it's Oztix white-labelled under a custom domain, same client-rendered problem as Oztix itself. Megatix (megatix.com.au) is where both actually sell tickets, found via web search, not the promoter sites.
- Megatix's own `/events` browse page is itself a Nuxt.js SPA (`_nuxt/BrowseEvents...` bundle referenced, no server-rendered listing) — not crawlable, same problem as Oztix/AREP. Individual event pages (`/events/<slug>`) are server-rendered with real JSON-LD though, so this spike seeds from three known event URLs (two promoters) rather than a search endpoint.
- `robots.txt` has no AI-crawler disallow.
- No bot-management challenge observed — plain HTTP 200s on all seed event pages.
- Each event page embeds one `schema.org` `Event` JSON-LD block with `name`, `startDate`, `offers.price`, and `location.name`/`address`. `promoter` is not in the JSON-LD and is filled in from the seed list's own promoter label rather than scraped.
- `genre_tags` and `attendance_indicator` are not present in the JSON-LD and are not scraped from anywhere else — left unpopulated rather than guessed.

## Request outcomes

| Outcome | Count |
|---|---|
| 200 | 3 |

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

Price viable — Megatix closes the gap left by No Sleep Entertainment's and Dangerous Goods' own unusable sites. Same discovery caveat as Ticketbooth/Ticket Merchant: needs a maintained seed list, not a crawlable index.
