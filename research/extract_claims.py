"""
Extract factual claims, numbers, dates, and key statements from research text.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


def extract_claims(text: str, topic_summary: str = "") -> List[Dict[str, Any]]:
    """
    Extract discrete verifiable claims from research text and summaries.
    Filters out opinionated phrases and extracts statements containing factual assertions,
    statistics, measurements, or established historical/scientific findings.
    """
    combined = f"{topic_summary}\n{text}".strip()
    if not combined:
        return []

    # Split into candidate sentences
    raw_sentences = re.split(r"(?<=[.!?])\s+", combined)
    claims: List[Dict[str, Any]] = []

    # Patterns indicating high factual value (numbers, percentages, years, scientific terms)
    fact_patterns = [
        re.compile(r"\b\d+"),  # any numbers, e.g. 2, 72, 2024
        re.compile(r"\b(because|results in|demonstrated|discovered|measured|indicates|proven|shows|found|replace|promising|known as|refers to|used to|defined as|consists of|explains|leads to|creates|reduces|increases|operates|doubles|powers|affects|causes|occurs|formed|bias|effect|mechanism|study|research)\b", re.I),
        re.compile(r"\b(billion|million|trillion|percent|meters|kilometers|degrees|years|density|energy|risk|electrolytes)\b", re.I),
    ]

    # Patterns indicating subjective opinions to skip
    opinion_patterns = [
        re.compile(r"\b(in my opinion|i believe|i think|feel like|might be cool|awesome|must buy)\b", re.I),
    ]

    seen = set()

    for sent in raw_sentences:
        sent = sent.strip()
        if len(sent) < 25 or len(sent) > 280:
            continue

        if any(op.search(sent) for op in opinion_patterns):
            continue

        # Check if sentence has factual evidence patterns
        matches = sum(1 for fp in fact_patterns if fp.search(sent))
        if matches >= 1:
            clean = " ".join(sent.split())
            if clean.lower() not in seen:
                seen.add(clean.lower())
                claims.append({
                    "claim_text": clean,
                    "confidence_score": min(1.0, 0.5 + 0.2 * matches),
                    "contains_numbers": bool(re.search(r"\d", clean)),
                })

    return claims[:8]  # Limit to top relevant claims
