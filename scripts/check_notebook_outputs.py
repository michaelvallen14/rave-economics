"""Pre-commit guard: refuse notebooks with cell outputs still attached.

Committed outputs risk leaking data (e.g. HILDA head() calls) into git
history. Strip with `jupyter nbconvert --clear-output` or `nbstripout`
before committing. Bypass only with `git commit --no-verify`.
"""

from __future__ import annotations

import json
import subprocess
import sys


def staged_notebooks() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip().endswith(".ipynb")]


def has_output(path: str) -> bool:
    result = subprocess.run(
        ["git", "show", f":{path}"],
        capture_output=True,
        text=True,
        check=True,
    )
    notebook = json.loads(result.stdout)
    for cell in notebook.get("cells", []):
        if cell.get("outputs"):
            return True
        if cell.get("execution_count") is not None:
            return True
    return False


def main() -> int:
    dirty = [path for path in staged_notebooks() if has_output(path)]
    if not dirty:
        return 0

    print("BLOCKED: staged notebook(s) still have outputs or execution counts.")
    for path in dirty:
        print(f"  {path}")
    print("\nStrip outputs before committing, e.g.:")
    print("  uv run jupyter nbconvert --clear-output --inplace <notebook>")
    print("Bypass only with an explicit `git commit --no-verify`.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
