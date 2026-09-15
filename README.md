# rave-economics

Melbourne electronic music scene data, long-run outcome data (NLSY97), and a
scenario model that bridges the two — kept as three structurally separate
parts, described below.

## Limitations (read this before the sections below)

- **Part A (Resident Advisor scrape) is currently blocked.** ra.co sits
  behind DataDome bot-management that returns a CAPTCHA challenge (HTTP 403)
  to any plain HTTP client, independent of user agent. `robots.txt` also
  explicitly disallows `ClaudeBot` and `anthropic-ai` from the whole site.
  See [docs/ra-feasibility.md](docs/ra-feasibility.md) for the full spike
  result (0/50 events retrievable) — Part A has not been built and needs a
  different acquisition path before it can be.
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
- **Small, single-city, single-cohort data throughout.** Part A is Melbourne
  only; Part B is a single US birth cohort (NLSY97, born 1980-84). Neither
  generalises beyond its own population without a separate argument for why
  it should.

## What's here so far

This is a scaffold plus one completed feasibility check — see "Status"
below for exactly what's implemented.

- `src/ra/` — Part A: Melbourne RA event scraping and analysis (genre
  volume over time, venue concentration, artist/promoter co-occurrence
  network, ticket price deflated by ABS Wage Price Index)
- `src/nlsy97/` — Part B: NLSY97 lagged going-out/drinking vs. net worth
  analysis
- `src/model/` — Part C: the scenario model bridging A and B
- `sql/` — DuckDB is the SQL layer for this project
- `data/` — never committed; see `CLAUDE.md`
- `outputs/figures/`, `outputs/tables/` — committed aggregates only

## Status

Done this session: repo scaffold, data-handling rules and enforcement
(`CLAUDE.md`, pre-commit hooks), and the RA feasibility spike.

Not yet built: the RA scraper proper, the NLSY97 analysis, and the Part C
scenario model. Part A in particular needs a decision on acquisition
strategy before any scraper is written — see
[docs/ra-feasibility.md](docs/ra-feasibility.md).

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
