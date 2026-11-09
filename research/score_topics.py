"""
Topic scoring engine based on the 100-point model defined in Section 9.2.
Factors:
- Curiosity and surprise: 30 pts
- Visual potential: 25 pts
- Audience relevance: 20 pts
- Shareability: 15 pts
- Source reliability: 10 pts
Threshold: 70/100, plus mandatory verification pass.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


def score_topic(
    topic: Dict[str, Any],
    sources: List[Dict[str, Any]],
    claims: List[Dict[str, Any]]
) -> Dict[str, Any]:
    title = topic.get("title", "")
    summary = topic.get("summary", "")
    full_text = f"{title} {summary}"

    # 1. Curiosity and Surprise (Max 30)
    curiosity_keywords = ["why", "how", "secret", "mystery", "shocking", "hidden", "rule of", "paradox", "discovered", "unusual", "strange"]
    curiosity_matches = sum(1 for kw in curiosity_keywords if re.search(rf"\b{kw}\b", full_text, re.I))
    curiosity_score = min(30, 16 + (curiosity_matches * 5))

    # 2. Visual Potential (Max 25)
    visual_keywords = ["structure", "chart", "comparison", "battery", "brain", "energy", "earth", "space", "crater", "formula", "visual", "eye"]
    visual_matches = sum(1 for kw in visual_keywords if re.search(rf"\b{kw}\b", full_text, re.I))
    visual_score = min(25, 14 + (visual_matches * 4))

    # 3. Audience Relevance (Max 20)
    relevance_keywords = ["money", "habits", "decision", "future", "people", "invest", "psychology", "choice", "time", "world"]
    rel_matches = sum(1 for kw in relevance_keywords if re.search(rf"\b{kw}\b", full_text, re.I))
    relevance_score = min(20, 12 + (rel_matches * 3))

    # 4. Shareability (Max 15)
    # Actionable, intriguing, or surprising facts score high
    has_numbers = bool(re.search(r"\d+", full_text))
    shareability_score = 11 + (4 if has_numbers else 2)

    # 5. Source Reliability (Max 10)
    primary_sources = sum(1 for s in sources if s.get("source_class") == "primary")
    source_count = len(sources)
    if primary_sources > 0:
        source_score = 10
    elif source_count >= 2:
        source_score = 9
    elif source_count >= 1:
        source_score = 8
    else:
        source_score = 4

    total_score = curiosity_score + visual_score + relevance_score + shareability_score + source_score
    passed_threshold = total_score >= 70 and source_score >= 7

    return {
        "total_score": total_score,
        "passed_threshold": passed_threshold,
        "breakdown": {
            "curiosity": curiosity_score,
            "visual_potential": visual_score,
            "audience_relevance": relevance_score,
            "shareability": shareability_score,
            "source_reliability": source_score,
        }
    }
