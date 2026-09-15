# CLAUDE.md

Guidance for working in this repo. The data handling rules below are not
optional — they exist because HILDA is governed by an Australian Government
confidentiality deed carrying Criminal Code penalties for mishandling.

## Data handling rules

1. **No data file of any kind is ever committed to git.** GitHub is
   US-hosted, and the HILDA deed forbids transferring HILDA data outside
   Australia. This applies to every dataset in this repo, not just HILDA —
   NLSY97 raw files stay out of git too, for size reasons.
2. `data/` is entirely gitignored. `data/hilda/` is called out explicitly in
   `.gitignore` even though `data/` alone already covers it, because HILDA is
   the dataset where a mistake has legal consequences.
3. HILDA outputs may be committed **only as aggregates**: charts, regression
   tables, summary statistics. Never rows, never samples, never `head()`
   output in a committed notebook. If you can look at a committed file and
   reconstruct a single respondent's record, it should not be committed.
4. **Never join HILDA to any other dataset at record level.** The deed
   forbids linkage without written consent. This includes joining HILDA to
   NLSY97, to RA scrape data, or to anything else — Part C's scenario model
   bridges A and B qualitatively/illustratively, never via a data join, and
   HILDA (if and when approved) follows the same rule.
5. NLSY97 is public use and has none of the above restrictions, but keep raw
   files out of `data/` -> git anyway; it's a size/hygiene rule, not a legal
   one.
6. HILDA has **not been approved for use in this project yet**. Do not
   write code that reads, processes, or references HILDA data files until
   that changes.

## Enforcement

A `pre-commit` hook (`.pre-commit-config.yaml`, wired into
`.git/hooks/pre-commit` via `uv run pre-commit install`) refuses any commit
where a staged file:

- is under `data/`
- has extension `.dta`, `.sav`, `.sas7bdat`, `.por`, `.zip`, `.csv`, `.parquet`
- has `hilda` anywhere in its path (case-insensitive)

A second hook refuses any staged `.ipynb` that still has cell outputs or
execution counts attached — strip with
`uv run jupyter nbconvert --clear-output --inplace <notebook>` before
committing.

**The only bypass is an explicit `git commit --no-verify`.** There is no
config flag, no allowlist, no "just this once" path. If you find yourself
reaching for `--no-verify`, stop and check you actually mean to commit a
data file, because the answer under rule 1 is always no — `--no-verify`
exists for cases like a hook false-positiving on a filename, not for
overriding the data rule itself.

## Project structure

Three parts are kept structurally separate — do not blur them:

- `src/ra/` — Part A, Australian electronic music/rave scene (multi-source
  ticketing-platform scrape + analysis — ra.co is blocked; Moshtix,
  Ticketbooth/Leap Events and Ticket Merchant passed feasibility instead,
  see README.md's Limitations section)
- `src/nlsy97/` — Part B, NLSY97 long-run outcomes analysis
- `src/model/` — Part C, the scenario model bridging A and B. This is
  explicitly **not** a join and **not** a causal claim — it's a scenario
  tool, and code/docs in here should keep saying so rather than letting that
  framing erode over time.

DuckDB (`sql/`) is the SQL layer. `outputs/figures/` and `outputs/tables/`
are committed (aggregates only, per the HILDA rule above); `data/` never is.

## Working conventions

- Short functions, type hints, no notebook-only logic — anything that runs
  more than once belongs in `src/`, called from a thin notebook cell if
  needed.
- Every script runnable from the command line (`argparse`, a `main()`, a
  `__main__` guard).
- `uv run <command>` for anything that needs the project's dependencies.
