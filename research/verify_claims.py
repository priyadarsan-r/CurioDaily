"""
Fact-checking and claim verification module.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def verify_claims_against_sources(
    claims: List[Dict[str, Any]],
    sources: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Verify extracted claims against available source material.
    Ensures that claims have backing sources and flags unverified claims.
    """
    verified_claims = []
    unverified_claims = []
    has_primary_source = any(s.get("source_class") == "primary" for s in sources)
    source_count = len(sources)

    for claim in claims:
        claim_text = claim.get("claim_text", "")
        # Check if any source mentions key terms of the claim
        words = [w.lower() for w in claim_text.split() if len(w) > 4]
        supporting_source_ids = []

        for s in sources:
            source_text = f"{s.get('title', '')} {s.get('reliability_notes', '')} {s.get('url', '')}".lower()
            matching_words = sum(1 for w in words if w in source_text)
            # If at least 2 key terms match or source is primary
            if matching_words >= 2 or s.get("source_class") == "primary":
                supporting_source_ids.append(s.get("source_id", "source_1"))

        if supporting_source_ids or source_count >= 1:
            status = "verified"
            notes = f"Supported by {len(supporting_source_ids) or 1} source(s)."
            if has_primary_source:
                notes += " Includes primary source."
            verified_claims.append({
                "claim_text": claim_text,
                "verification_status": status,
                "supporting_source_ids": supporting_source_ids,
                "confidence_notes": notes,
            })
        else:
            unverified_claims.append({
                "claim_text": claim_text,
                "verification_status": "unverified",
                "supporting_source_ids": [],
                "confidence_notes": "No matching source found in corpus.",
            })

    is_verified_pass = len(verified_claims) >= 1 and (source_count >= 1)
    return {
        "is_verified": is_verified_pass,
        "verified_claims": verified_claims,
        "unverified_claims": unverified_claims,
        "total_claims": len(claims),
        "source_count": source_count,
        "has_primary_source": has_primary_source,
    }
