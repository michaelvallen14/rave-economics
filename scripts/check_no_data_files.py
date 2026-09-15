"""Pre-commit guard: refuse to commit data files or anything HILDA-related.

See CLAUDE.md for the rules this enforces. Bypass only with
`git commit --no-verify`, and only for a deliberate, reviewed reason.
"""

from __future__ import annotations

import subprocess
import sys

BLOCKED_EXTENSIONS = {".dta", ".sav", ".sas7bdat", ".por", ".zip", ".csv", ".parquet"}
BLOCKED_PREFIX = "data/"


def staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def violation(path: str) -> str | None:
    lower = path.lower()
    if lower.startswith(BLOCKED_PREFIX):
        return f"under {BLOCKED_PREFIX}"
    ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path.rsplit("/", 1)[-1] else ""
    if ext in BLOCKED_EXTENSIONS:
        return f"has blocked extension {ext}"
    if "hilda" in lower:
        return "path contains 'hilda'"
    return None


def main() -> int:
    problems = [(path, reason) for path in staged_files() if (reason := violation(path))]
    if not problems:
        return 0

    print("BLOCKED: staged file(s) look like data, which must never be committed.")
    print("See CLAUDE.md — data/ (HILDA especially) never leaves this machine via git.\n")
    for path, reason in problems:
        print(f"  {path}  [{reason}]")
    print("\nIf a staged file is a false positive, unstage it or rename it.")
    print("Bypass only with an explicit `git commit --no-verify`.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
