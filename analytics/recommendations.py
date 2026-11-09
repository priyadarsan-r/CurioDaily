"""
Weekly optimization and editorial recommendations engine.
Implements the continuous improvement loop defined in Section 17.3.
"""

from __future__ import annotations

from typing import Any, Dict, List
from analytics.aggregate import aggregate_insights_by_format, aggregate_insights_by_pillar
from database.db import Database


def generate_recommendations(db: Database) -> List[Dict[str, str]]:
    by_pillar = aggregate_insights_by_pillar(db)
    by_format = aggregate_insights_by_format(db)
    recommendations: List[Dict[str, str]] = []

    if not by_pillar and not by_format:
        recommendations.append({
            "type": "baseline",
            "message": "Insufficient publishing data yet. Continue adhering to the 4 Reels + 2 Posts + 1 Carousel baseline for 14 days."
        })
        return recommendations

    # Find highest engaging pillar
    best_pillar = None
    best_saves = -1
    for pillar, data in by_pillar.items():
        saves = data.get("total_saves", 0)
        if saves > best_saves:
            best_saves = saves
            best_pillar = pillar

    if best_pillar:
        recommendations.append({
            "type": "pillar_priority",
            "message": f"Pillar '{best_pillar}' generated the highest save rate ({best_saves} saves). Prioritize topics with actionable frameworks in this category."
        })

    # Format comparison
    carousel_data = by_format.get("carousel", {})
    reel_data = by_format.get("reel", {})
    if carousel_data.get("total_saves", 0) > reel_data.get("total_saves", 0):
        recommendations.append({
            "type": "format_insight",
            "message": "Carousels are driving higher save rates than Reels. Consider expanding successful Reel concepts into multi-slide step-by-step deep dives."
        })

    return recommendations
