# rave-economics

Australian electronic music/rave scene data, long-run outcome data (NLSY97),
and a scenario model that bridges the two — kept as three structurally
separate parts, described below.

## Limitations (read this before the sections below)

- **Part A is Australia-wide, multi-source, and still acquisition-only.**
  The original plan (ra.co) is blocked: ra.co sits behind DataDome
  bot-management that returns a CAPTCHA challenge (HTTP 403) to any plain
  HTTP client, independent of user agent, and its `robots.txt` explicitly
  disallows `ClaudeBot`/`anthropic-ai` from the whole site. See
  [docs/ra-feasibility.md](docs/ra-feasibility.md) (0/50 events
  retrievable). Three replacement sources passed feasibility instead:
  - **Moshtix** — [docs/moshtix-feasibility.md](docs/moshtix-feasibility.md),
    GO (64% price completeness). Mainstream club/dance circuit; its
    `location=melbourne` search parameter doesn't reliably geo-filter (a
    fair few non-Melbourne venues came back), so real acquisition needs to
    filter on the JSON-LD's own address fields instead of trusting the
    search UI.
  - **Ticketbooth/Leap Events** —
    [docs/ticketbooth-feasibility.md](docs/ticketbooth-feasibility.md), GO
    (60% price completeness). Hosts MASIF, HSU's Knockout, Symbiotic, and
    Ultra Australia. Has no crawlable listing page (root 403, `/events`
    404) — needs a maintained seed list of promoter pages, not a single
    search endpoint like Moshtix's.
  - **Ticket Merchant** —
    [docs/ticketmerchant-feasibility.md](docs/ticketmerchant-feasibility.md),
    GO (confirmed via Teletech). It's a **secondary/resale marketplace**
    (`"category": "Secondary"` in its own JSON-LD), so its prices may sit
    above face value — relevant if this source ever feeds a
    price/inflation analysis rather than just volume/venue/lineup.
  - **Megatix** —
    [docs/megatix-feasibility.md](docs/megatix-feasibility.md), GO
    (confirmed via No Sleep Entertainment). Their own site
    (nosleepent.com.au) is a client-rendered dead end, but Megatix is
    where they actually sell tickets. Same caveat as Ticketbooth/Ticket
    Merchant: Megatix's own `/events` browse page is a client-rendered
    Nuxt.js SPA, so this needs a seed list too, not a crawlable index.
  - **Confirmed dead ends** (client-side rendered SPA — no data without a
    real browser, out of scope per this project's no-evasion stance):
    Oztix, AREP (HSU's EPIK event), eventflo.io (Symbiotic's MARLO event),
    and No Sleep Entertainment's own site.
  - None of the above has been turned into a real scraper yet — these are
    all feasibility spikes only.
- **Part B is not causal.** It's a lagged-design association (drinking
  frequency at 19-22 predicting net worth at 33-38, controlling for
  education, parental income and own income at 22), not a causal estimate.
  Selection into "high going-out" at 19-22 is not random, and the controls
  used don't rule that out.
- **Part C is a scenario model, not a join and not a causal claim.** It
  does not link any individual's RA activity to any individual's NLSY97 (or
  future HILDA) outcome. Record-level linkage between HILDA and any other
  dataset is forbidden by the HILDA deed regardless, and NLSY97 (US) and RA
  Melbourne (Australia) are different populations entirely — Part C
  illustrates a plausible scenario, it does not estimate an effect.
- **HILDA is not yet approved for this project.** It is referenced in
  `CLAUDE.md`'s data rules pre-emptively, in case approval comes through
  later, but no HILDA code or data exists in this repo yet.
- **Single-cohort data for Part B.** Part B is a single US birth cohort
  (NLSY97, born 1980-84) and doesn't generalise beyond it without a
  separate argument for why it should. Part A is now Australia-wide, not
  Melbourne-only (see above).

## What's here so far

This is a scaffold plus several completed feasibility checks — see
"Status" below for exactly what's implemented.

- `src/ra/` — Part A: Australian rave/dance-event scraping (multi-source:
  Moshtix, Ticketbooth/Leap Events, Ticket Merchant — see Limitations
  above) and analysis (genre volume over time, venue concentration,
  artist/promoter co-occurrence network, ticket price deflated by ABS Wage
  Price Index)
- `src/nlsy97/` — Part B: NLSY97 lagged going-out/drinking vs. net worth
  analysis
- `src/model/` — Part C: the scenario model bridging A and B
- `sql/` — DuckDB is the SQL layer for this project
- `data/` — never committed; see `CLAUDE.md`
- `outputs/figures/`, `outputs/tables/` — committed aggregates only

## Status

Done this session: repo scaffold, data-handling rules and enforcement
(`CLAUDE.md`, pre-commit hooks), and feasibility spikes for five
ticketing sources (ra.co, Moshtix, Ticketbooth/Leap Events, Ticket
Merchant, Megatix).

Not yet built: the real Part A scraper (each spike above is feasibility
only, not a production scraper), the NLSY97 analysis, and the Part C
scenario model. Next for Part A: build the Moshtix/Ticketbooth/Ticket
Merchant/Megatix scrapers for real, with the geo-filter fix (Moshtix) and
seed-list maintenance (the other three) noted above.

## Setup

```
uv sync
uv run pre-commit install
```

## Data handling

See [CLAUDE.md](CLAUDE.md) — short version: no data file is ever committed,
`data/` is gitignored, HILDA outputs are aggregates-only if and when HILDA
is approved, and a pre-commit hook enforces both (bypass only with an
explicit `git commit --no-verify`).
