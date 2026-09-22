"""Genre classification for Part A: tag each scraped event as "harder
styles" (hardstyle, rawstyle, uptempo/frenchcore, hard techno, hard
trance, gabber) or not, based on keyword matches against the event's own
name and lineup text.

This is keyword-based, not a curated genre database, so it's a precision-
first, not recall-first, classifier: an event only gets tagged if the
harder-styles signal shows up literally in its name or lineup text (e.g.
a subgenre word, or a known harder-styles artist's name). Real events in
the scene that don't spell out a subgenre or headline a known artist will
be missed — this undercounts rather than overcounts.

KEYWORDS and ARTISTS are both maintained lists, like seeds.py — expect to
add to both as new subgenre terms or artists come up.
"""

from __future__ import annotations

import re

# Megatix ceiling (checked 2026-09-22): its server-rendered HTML carries
# no description, meta description, or embedded state blob at all — it's
# a client-rendered Nuxt.js SPA (see docs/megatix-feasibility.md), so
# description-based matching only helps Ticketbooth/Leap Events and
# Moshtix. Megatix recall is capped at whatever's literally in the event
# name until/unless real browser rendering is used, which is out of scope
# per this project's no-evasion stance.

KEYWORDS = [
    "hardstyle",
    "rawstyle",
    "uptempo",
    "frenchcore",
    "hardcore",
    "hard techno",
    "hard trance",
    "hard dance",
    "gabber",
    "harder styles",
]

# Well-known harder-styles artists, for events whose name/lineup names an
# artist rather than spelling out a subgenre. Non-exhaustive by design —
# add to this as real seed events surface more names.
ARTISTS = [
    "audiofreq",
    "headhunterz",
    "wildstylez",
    "sub zero project",
    "angerfist",
    "miss k8",
    "da tweekaz",
    "coone",
    "adaro",
    "warface",
    "reinier zonneveld",
    "i hate models",
    "ansome",
]

_TERMS = [re.escape(term) for term in KEYWORDS + ARTISTS]
_PATTERN = re.compile(r"\b(" + "|".join(_TERMS) + r")\b", re.IGNORECASE)


def classify_genre(name: str | None, lineup: str | None, description: str | None = None) -> str | None:
    """Return a comma-joined list of matched harder-styles terms found in
    the event name, lineup, and/or description, or None if nothing
    matched. description matters in practice: several sources (e.g.
    Ticketbooth/Leap Events) leave JSON-LD's performer field empty but
    write the actual subgenre ("Hardstyle & Raw", "Happy Hard") into the
    event description instead."""
    text = " ".join(t for t in (name, lineup, description) if t)
    if not text:
        return None
    matches = dict.fromkeys(m.lower() for m in _PATTERN.findall(text))
    return ", ".join(matches) if matches else None
