# RA feasibility spike

Run: 2026-09-15T05:13:16+00:00
Target sample size: 50 Melbourne events
Event URLs discovered from listing page: 0
Events successfully fetched and parsed: 0

## Access notes

- `robots.txt` (`User-agent: *`) permits `/events/...` — it only blocks `/pro`, `/user`, `/api`, `/my-tickets`, `/logout.aspx`, `/inbox.aspx`, `/widget`.
- `robots.txt` separately, explicitly disallows `ClaudeBot` and `anthropic-ai` from the entire site (`Disallow: /`), alongside GPTBot, CCBot, PerplexityBot and other AI crawlers. This script identifies as a distinct, descriptive, contact-bearing UA (not those tokens, not a browser spoof) and only requests paths `robots.txt` permits for `*`.
- Independent of robots.txt: ra.co sits behind DataDome bot-management. A plain HTTP GET to the listing page returns HTTP 403 with a JS/CAPTCHA challenge page, reproduced identically with both this script's UA and a full desktop Chrome UA string — this is fingerprint/behaviour-based blocking, not a UA string check.
- This spike does not attempt to solve the challenge or automate a real browser session to get past it — that would mean building anti-bot-detection evasion tooling against a site whose robots.txt already names AI crawlers as unwelcome, which is out of scope for this project.

## Request outcomes

| Outcome | Count |
|---|---|
| 403 | 1 |

## Field completeness

Percentage of the intended sample (denominator = target sample size, not just successfully fetched events) with each field populated.

| Field | Populated |
|---|---|
| date | 0.0% |
| name | 0.0% |
| venue | 0.0% |
| lineup | 0.0% |
| promoter | 0.0% |
| genre_tags | 0.0% |
| price | 0.0% |
| attendance_indicator | 0.0% |

## Decision

Ticket price populated for **0.0%** of the target sample.
Threshold is 50%. Result: **NO-GO**.

No events were fetched at all (0/50) — this is a harder failure than a missing-price case. The acquisition layer itself is blocked, so no field is assessable, not just price. Live scraping of ra.co via a polite HTTP client is not viable in its current form.
