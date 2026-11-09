"""
Fetch insights and performance metrics for published content from Meta Graph API.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
import requests

from database.db import Database

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


def fetch_media_insights(
    media_id: str,
    access_token: Optional[str] = None
) -> Dict[str, Any]:
    token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN")
    if not token or media_id.startswith("mock_"):
        # Deterministic mock metrics for testing/dry-run
        return {
            "reach": 1250,
            "plays": 1820,
            "likes": 94,
            "comments": 12,
            "shares": 28,
            "saves": 45,
            "follows": 5,
        }

    url = f"{GRAPH_API_BASE}/{media_id}/insights"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"metric": "reach,saved,shares,comments,likes,plays"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            metrics: Dict[str, int] = {}
            for item in data.get("data", []):
                name = item.get("name")
                val = item.get("values", [{}])[0].get("value", 0)
                metrics[name] = val
            return {
                "reach": metrics.get("reach", 0),
                "plays": metrics.get("plays", 0),
                "likes": metrics.get("likes", 0),
                "comments": metrics.get("comments", 0),
                "shares": metrics.get("shares", 0),
                "saves": metrics.get("saved", 0),
                "follows": 0,
            }
        logger.warning("Failed fetching insights for media %s: %s", media_id, resp.text)
    except Exception as exc:
        logger.warning("Error calling insights API: %s", exc)

    return {"reach": 0, "plays": 0, "likes": 0, "comments": 0, "shares": 0, "saves": 0, "follows": 0}


def sync_all_published_insights(db: Database) -> int:
    """Fetch and update metrics for all published items."""
    sql = "SELECT DISTINCT content_id, instagram_media_id FROM publishing_queue WHERE status = 'published' AND instagram_media_id IS NOT NULL;"
    synced = 0
    with db.get_connection() as conn:
        rows = conn.execute(sql).fetchall()

    for row in rows:
        content_id = row["content_id"]
        media_id = row["instagram_media_id"]
        metrics = fetch_media_insights(media_id)
        db.record_insights(content_id, metrics)
        synced += 1

    return synced
