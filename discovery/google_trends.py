"""
Google Trends public RSS discovery adapter.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
import feedparser

logger = logging.getLogger(__name__)

TRENDS_RSS_URL = "https://trends.google.com/trending/rss?geo={geo}"


def fetch_google_trends(geo: str = "US", category: str = "money_secrets", limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch daily trending topics from Google Trends public RSS feed."""
    url = TRENDS_RSS_URL.format(geo=geo)
    candidates: List[Dict[str, Any]] = []

    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:limit]:
            title = entry.get("title", "").strip()
            if not title:
                continue

            summary = entry.get("summary", "") or entry.get("description", "")
            source_url = entry.get("link", "")
            pub_date = entry.get("published", datetime.now(timezone.utc).isoformat())

            candidates.append({
                "title": title,
                "summary": summary,
                "category": category,
                "source_url": source_url,
                "source_type": "google_trends",
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "published_at": pub_date,
            })
    except Exception as exc:
        logger.warning("Failed to fetch Google Trends for geo %s: %s", geo, exc)

    return candidates
