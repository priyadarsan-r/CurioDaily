"""
NASA public feed discovery adapter.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
import feedparser

logger = logging.getLogger(__name__)

NASA_NEWS_RSS = "https://www.nasa.gov/news-release/feed/"


def fetch_nasa_news(limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch updates from NASA's public news release RSS feed."""
    candidates: List[Dict[str, Any]] = []

    try:
        feed = feedparser.parse(NASA_NEWS_RSS)
        for entry in feed.entries[:limit]:
            title = entry.get("title", "").strip()
            if not title:
                continue

            summary = entry.get("summary", "") or entry.get("description", "")
            source_url = entry.get("link", "")
            pub_date = entry.get("published", datetime.now(timezone.utc).isoformat())

            candidates.append({
                "title": title,
                "summary": summary[:500],
                "category": "future_is_here",
                "source_url": source_url,
                "source_type": "nasa",
                "publisher": "NASA",
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "published_at": pub_date,
            })
    except Exception as exc:
        logger.warning("Error fetching NASA RSS: %s", exc)

    return candidates
