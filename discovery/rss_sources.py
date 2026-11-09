"""
RSS/Atom feeds discovery adapter.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
import feedparser

logger = logging.getLogger(__name__)


def fetch_rss_feed(
    feed_url: str,
    category: str,
    source_name: str = "",
    limit: int = 15
) -> List[Dict[str, Any]]:
    """Parse public RSS or Atom feed and extract candidate topic entries."""
    candidates: List[Dict[str, Any]] = []

    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:limit]:
            title = entry.get("title", "").strip()
            if not title:
                continue

            summary = entry.get("summary", "") or entry.get("description", "")
            # Basic cleanup of HTML tags if present in summary
            if "<" in summary and ">" in summary:
                from bs4 import BeautifulSoup
                summary = BeautifulSoup(summary, "html.parser").get_text().strip()

            source_url = entry.get("link", "")
            pub_date = entry.get("published", datetime.now(timezone.utc).isoformat())

            candidates.append({
                "title": title,
                "summary": summary[:500],
                "category": category,
                "source_url": source_url,
                "source_type": "rss",
                "publisher": source_name,
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "published_at": pub_date,
            })
    except Exception as exc:
        logger.warning("Error fetching RSS feed %s: %s", feed_url, exc)

    return candidates
