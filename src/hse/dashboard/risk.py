from __future__ import annotations

import re
from dataclasses import dataclass

FORBIDDEN_PUBLIC_TERMS = (
    "ai",
    "hermes",
    "hse",
    "workflow",
    "tool",
    "system",
    "automation",
    "engine",
    "money printer",
    "printer",
    "machine that prints",
    "prints money",
)

_PATTERN = re.compile(r"\b(" + "|".join(re.escape(t) for t in FORBIDDEN_PUBLIC_TERMS) + r")\b", re.IGNORECASE)


@dataclass(frozen=True)
class MetadataRisk:
    blocked: bool
    matches: list[str]


def scan_public_metadata(text: str) -> MetadataRisk:
    matches = sorted({m.group(0).lower() for m in _PATTERN.finditer(text or "")})
    return MetadataRisk(blocked=bool(matches), matches=matches)
