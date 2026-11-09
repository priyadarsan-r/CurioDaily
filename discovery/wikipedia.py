"""
Wikipedia public API discovery adapter.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
import requests

logger = logging.getLogger(__name__)

USER_AGENT = "CurioDailyContentBot/1.0 (Educational Content Engine; contact@curiodaily.org)"
WIKI_RANDOM_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/random/summary"


def fetch_wikipedia_curiosities(limit: int = 5, category: str = "daily_mystery") -> List[Dict[str, Any]]:
    """Fetch interesting topics from Wikipedia's public REST summary API."""
    candidates: List[Dict[str, Any]] = []
    headers = {"User-Agent": USER_AGENT}

    for _ in range(limit):
        try:
            resp = requests.get(WIKI_RANDOM_SUMMARY_URL, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("title", "")
                extract = data.get("extract", "")
                content_urls = data.get("content_urls", {}).get("desktop", {})
                page_url = content_urls.get("page", f"https://en.wikipedia.org/wiki/{title}")

                if title and extract and len(extract) > 100:
                    candidates.append({
                        "title": title,
                        "summary": extract[:500],
                        "category": category,
                        "source_url": page_url,
                        "source_type": "wikipedia",
                        "publisher": "Wikipedia",
                        "discovered_at": datetime.now(timezone.utc).isoformat(),
                    })
        except Exception as exc:
            logger.warning("Error fetching Wikipedia summary: %s", exc)

    return candidates
