"""
Aggregates performance metrics across content pillars and formats.
"""

from __future__ import annotations

from typing import Any, Dict, List
from database.db import Database


def aggregate_insights_by_pillar(db: Database) -> Dict[str, Dict[str, Any]]:
    """Aggregate total reach, likes, saves, shares by pillar."""
    sql = """
    SELECT c.category,
           COUNT(i.insight_id) as total_posts,
           SUM(i.reach) as total_reach,
           SUM(i.plays) as total_plays,
           SUM(i.likes) as total_likes,
           SUM(i.shares) as total_shares,
           SUM(i.saves) as total_saves
    FROM insights i
    JOIN content c ON i.content_id = c.content_id
    GROUP BY c.category;
    """
    results: Dict[str, Dict[str, Any]] = {}
    with db.get_connection() as conn:
        rows = conn.execute(sql).fetchall()
        for r in rows:
            results[r["category"]] = {
                "total_posts": r["total_posts"],
                "total_reach": r["total_reach"] or 0,
                "total_plays": r["total_plays"] or 0,
                "total_likes": r["total_likes"] or 0,
                "total_shares": r["total_shares"] or 0,
                "total_saves": r["total_saves"] or 0,
            }
    return results


def aggregate_insights_by_format(db: Database) -> Dict[str, Dict[str, Any]]:
    """Aggregate total reach, likes, saves, shares by format (reel, image, carousel)."""
    sql = """
    SELECT c.format,
           COUNT(i.insight_id) as total_posts,
           SUM(i.reach) as total_reach,
           SUM(i.plays) as total_plays,
           SUM(i.likes) as total_likes,
           SUM(i.shares) as total_shares,
           SUM(i.saves) as total_saves
    FROM insights i
    JOIN content c ON i.content_id = c.content_id
    GROUP BY c.format;
    """
    results: Dict[str, Dict[str, Any]] = {}
    with db.get_connection() as conn:
        rows = conn.execute(sql).fetchall()
        for r in rows:
            results[r["format"]] = {
                "total_posts": r["total_posts"],
                "total_reach": r["total_reach"] or 0,
                "total_plays": r["total_plays"] or 0,
                "total_likes": r["total_likes"] or 0,
                "total_shares": r["total_shares"] or 0,
                "total_saves": r["total_saves"] or 0,
            }
    return results
