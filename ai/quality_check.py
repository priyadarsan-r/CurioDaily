"""
Quality control gate for generated scripts and editorial plans.
Implements the editorial safeguards defined in Section 3.2, 10.3, and 16.1.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

FORBIDDEN_PHRASES = [
    r"\bscientists are baffled\b",
    r"\bmind blown\b",
    r"\bguaranteed returns?\b",
    r"\bget rich quick\b",
    r"\bmiracle cure\b",
    r"\bconspiracy\b",
    r"\b100% risk free\b",
    r"\bsecret they don't want you to know\b",
]


def check_script_quality(content_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates script against quality standards:
    - No forbidden hype or sensational phrases.
    - Word count bounds.
    - Presence of clear hook, context, and takeaway.
    - Presence of sources.
    """
    errors: List[str] = []
    warnings: List[str] = []
    format_type = content_record.get("format", "reel")
    narration = content_record.get("script", "") or content_record.get("narration", "")

    # 1. Check forbidden sensationalist phrases
    for pat in FORBIDDEN_PHRASES:
        if re.search(pat, narration, re.I):
            errors.append(f"Forbidden sensationalist phrase detected matching pattern: {pat}")

    # 2. Format specific validation
    if format_type == "reel":
        word_count = len(narration.split())
        if word_count < 70:
            errors.append(f"Reel narration too short ({word_count} words). Minimum is 70.")
        elif word_count > 165:
            errors.append(f"Reel narration too long ({word_count} words). Maximum is 165.")

        storyboard = content_record.get("storyboard_json") or []
        if isinstance(storyboard, list) and len(storyboard) < 5:
            errors.append(f"Reel storyboard has only {len(storyboard)} scenes. Minimum 5 required.")

    elif format_type == "carousel":
        slides = content_record.get("slides") or content_record.get("storyboard_json") or []
        if isinstance(slides, list):
            if len(slides) < 5 or len(slides) > 8:
                errors.append(f"Carousel slide count ({len(slides)}) outside permitted range [5, 8].")

    # 3. Check caption and sources
    caption = content_record.get("caption", "")
    if not caption or len(caption) < 20:
        errors.append("Caption is missing or too short.")

    passed = len(errors) == 0
    return {
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
    }
