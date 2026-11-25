"""Content policy checks for the archived site snapshot."""

from __future__ import annotations

from pathlib import Path

CONTENT_JSON = Path(__file__).resolve().parent.parent / "site" / "content.json"

# Organizations that asked to be removed from every page of the site.
REMOVED_ORGANIZATION_NAMES = ("ネットワールド", "Networld", "NETWORLD")


def test_removed_organizations_do_not_appear_in_content() -> None:
    text = CONTENT_JSON.read_text(encoding="utf-8")
    found = [
        name for name in REMOVED_ORGANIZATION_NAMES if name.lower() in text.lower()
    ]
    assert found == []
