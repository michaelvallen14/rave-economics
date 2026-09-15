# Ticketbooth/Leap Events feasibility spike

Run: 2026-09-15T07:28:53+00:00
Target sample size: 5 events
Event URLs discovered: 5
Events successfully fetched and parsed: 5

## Access notes

- No public browse/search page: `events.ticketbooth.com.au/` and `events.leapevents.com/` both return 403 on the bare root, and `/events` returns 404 on both. Individual event pages (`/event/<slug>` or `/tickets/<slug>`) work fine — there just isn't an index to crawl.
- This spike therefore uses a curated seed list of 5 known events across 4 promoters (MASIF, HSU, Symbiotic x2, Ultra Australia), found by reading promoter pages' outbound links or web search — not discovered from the platform itself. A production version would need a maintained list of promoter pages to poll, not a single listing endpoint like Moshtix's search.
- `robots.txt` on both hostnames is a standard e-commerce boilerplate (login/checkout/dashboard paths) with no AI-crawler disallow.
- No bot-management challenge observed — plain HTTP 200s on every event page tried.
- Each event page embeds one `schema.org` `Event` JSON-LD block with `name`, `startDate`, `offers[].price`, and `location.name`/`address`. `promoter` is filled from the JSON-LD `organizer.name` where present, falling back to the promoter name from the seed list.
- `genre_tags` and `attendance_indicator` are not present in the JSON-LD and are not scraped from anywhere else — left unpopulated rather than guessed.

## Request outcomes

| Outcome | Count |
|---|---|
| 200 | 5 |

## Field completeness

Percentage of the intended sample (denominator = target sample size, not just successfully fetched events) with each field populated.

| Field | Populated |
|---|---|
| date | 80.0% |
| name | 80.0% |
| venue | 80.0% |
| lineup | 0.0% |
| promoter | 100.0% |
| genre_tags | 0.0% |
| price | 60.0% |
| attendance_indicator | 0.0% |

## Decision

Ticket price populated for **60.0%** of the target sample.
Threshold is 50%. Result: **GO**.

Price viable across MASIF, HSU, Symbiotic and Ultra Australia — Ticketbooth/Leap Events is a genuine multi-promoter source for the harder-styles/rave segment, not just one brand. Discovery is the open problem, not access: this platform needs a maintained list of promoter pages to poll rather than a single crawlable listing.
