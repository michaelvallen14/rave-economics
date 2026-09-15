"""Curated seed URLs for the three ticketing platforms that have no
crawlable listing page (Ticketbooth/Leap Events, Ticket Merchant,
Megatix — see docs/ticketbooth-feasibility.md, docs/ticketmerchant-
feasibility.md, docs/megatix-feasibility.md for why). Moshtix is the one
source that's crawled directly (src/ra/scrape_moshtix.py) rather than
seeded, since its search+category endpoint actually works.

This is real ongoing maintenance, not a one-time list: every event here
was found by reading a promoter's own page or a web search, not by the
platform itself. New events need adding by hand as they're announced.

Each entry is (platform, promoter, url, multi_event) — multi_event=True
means the page embeds one JSON-LD block per tour date (e.g. a Ticket
Merchant artist landing page) rather than a single event.
"""

from __future__ import annotations

SEEDS = [
    # Ticketbooth / Leap Events (events.ticketbooth.com.au, events.leapevents.com)
    ("ticketbooth", "MASIF", "https://events.ticketbooth.com.au/event/masif-presents-audiofreq-2024", False),
    ("ticketbooth", "HSU", "https://events.ticketbooth.com.au/event/knockout-outdoor-2026-level-up", False),
    ("ticketbooth", "Symbiotic", "https://events.ticketbooth.com.au/tickets/transmission-elysium-aus-2024", False),
    ("ticketbooth", "Symbiotic", "https://events.ticketbooth.com.au/tickets/hyperdome-2024", False),
    ("ticketbooth", "Ultra Australia", "https://events.leapevents.com/tickets/ultra-australia-2026", False),
    ("ticketbooth", "BPM Events", "https://events.leapevents.com/event/meltdown-festival-2026", False),
    # Ticket Merchant (theticketmerchant.com.au) — landing pages, one JSON-LD
    # block per tour date.
    ("ticketmerchant", "Teletech", "https://www.theticketmerchant.com.au/concert-tickets/teletech-tickets", True),
    # Megatix (megatix.com.au)
    ("megatix", "No Sleep Entertainment", "https://megatix.com.au/events/the-uprising", False),
    (
        "megatix",
        "No Sleep Entertainment",
        "https://megatix.com.au/events/rave-arcade-no-sleep-entertainment-4th-birthday",
        False,
    ),
    (
        "megatix",
        "Dangerous Goods Entertainment",
        "https://megatix.com.au/events/dangerous-goods-6-xxl-early-access-save-130",
        False,
    ),
]
