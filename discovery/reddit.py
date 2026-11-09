"""
Reddit public JSON discovery adapter.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
import requests

logger = logging.getLogger(__name__)

USER_AGENT = "CurioDailyContentBot/1.0 (Educational Content Engine)"


def fetch_reddit_topics(
    subreddit: str,
    category: str,
    limit: int = 15,
    min_score: int = 50
) -> List[Dict[str, Any]]:
    """
    Fetch trending or popular topics from a subreddit using public JSON endpoints.
    No authentication required for public subreddits with polite rate limiting.
    """
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    headers = {"User-Agent": USER_AGENT}
    candidates: List[Dict[str, Any]] = []

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.warning("Reddit returned status %s for r/%s", resp.status_code, subreddit)
            return candidates

        data = resp.json()
        children = data.get("data", {}).get("children", [])

        for child in children:
            post = child.get("data", {})
            if post.get("stickied") or post.get("over_18"):
                continue

            score = post.get("score", 0)
            if score < min_score:
                continue

            raw_title = post.get("title", "").strip()
            # Clean common prefixes like TIL (Today I Learned)
            if raw_title.lower().startswith("til that "):
                clean_title = raw_title[9:].strip()
            elif raw_title.lower().startswith("til : "):
                clean_title = raw_title[6:].strip()
            elif raw_title.lower().startswith("til "):
                clean_title = raw_title[4:].strip()
            else:
                clean_title = raw_title

            if clean_title:
                clean_title = clean_title[0].upper() + clean_title[1:]

            selftext = post.get("selftext", "")
            source_url = post.get("url") or f"https://www.reddit.com{post.get('permalink', '')}"

            candidates.append({
                "title": clean_title,
                "summary": selftext[:400] if selftext else clean_title,
                "category": category,
                "source_url": source_url,
                "source_type": "reddit",
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "engagement_score": score,
            })
    except Exception as exc:
        logger.warning("Error fetching Reddit r/%s: %s", subreddit, exc)

    return candidates
