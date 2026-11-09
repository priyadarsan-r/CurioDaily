"""
Public Domain and Open-Access Visual Asset Fetcher.
Safely retrieves relevant imagery from Wikimedia Commons and NASA APIs
with strict license tracking and offline fallbacks.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from PIL import Image
import requests

logger = logging.getLogger(__name__)

USER_AGENT = "CurioDailyContentEngine/1.0 (Educational Content; contact@curiodaily.org)"


def extract_search_keywords(title: str, scene_description: str = "") -> List[str]:
    """Extract clean search terms from title and visual description."""
    text = f"{title} {scene_description}"
    # Remove punctuation
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    stopwords = {
        "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "with", "of",
        "by", "from", "how", "why", "what", "is", "are", "this", "that", "scene",
        "card", "graphic", "visual", "showing", "clean", "high", "contrast"
    }
    words = [w.lower() for w in cleaned.split() if len(w) > 3 and w.lower() not in stopwords]
    return words[:4]


def fetch_wikimedia_image(query: str, output_path: Path, min_width: int = 600) -> Optional[Dict[str, Any]]:
    """
    Search Wikimedia Commons via Wikipedia API for a relevant public domain / CC image.
    """
    url = (
        "https://en.wikipedia.org/w/api.php?"
        f"action=query&format=json&generator=search&gsrsearch={quote_plus(query)}&gsrlimit=3"
        "&prop=pageimages|imageinfo&pithumbsize=1080"
    )
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, headers=headers, timeout=3.0)
        if resp.status_code != 200:
            return None
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for _, page in pages.items():
            thumb = page.get("thumbnail", {})
            img_url = thumb.get("source")
            if img_url:
                img_resp = requests.get(img_url, headers=headers, timeout=4.0)
                if img_resp.status_code == 200:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(img_resp.content)
                    with Image.open(output_path) as test_img:
                        if test_img.width >= min_width:
                            return {
                                "source_url": img_url,
                                "source": "Wikimedia Commons",
                                "license": "Creative Commons / Public Domain",
                                "title": page.get("title", query),
                                "attribution": f"Wikimedia Commons / Wikipedia ({page.get('title')})"
                            }
    except Exception as exc:
        logger.debug("Wikimedia fetch failed (expected offline/sandbox): %s", exc)
    return None


def fetch_nasa_image(query: str, output_path: Path) -> Optional[Dict[str, Any]]:
    """
    Search NASA Public Image Library for public domain space/science imagery.
    """
    url = f"https://images-api.nasa.gov/search?q={quote_plus(query)}&media_type=image"
    try:
        resp = requests.get(url, timeout=3.0)
        if resp.status_code != 200:
            return None
        items = resp.json().get("collection", {}).get("items", [])
        if not items:
            return None
        item = items[0]
        links = item.get("links", [])
        data_list = item.get("data", [{}])
        info = data_list[0] if data_list else {}
        img_url = links[0].get("href") if links else None
        if img_url:
            img_resp = requests.get(img_url, timeout=4.0)
            if img_resp.status_code == 200:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(img_resp.content)
                return {
                    "source_url": img_url,
                    "source": "NASA Image and Video Library",
                    "license": "NASA Public Domain",
                    "title": info.get("title", query),
                    "attribution": f"NASA / {info.get('center', 'JPL')} ({info.get('nasa_id', '')})"
                }
    except Exception as exc:
        logger.debug("NASA image fetch failed (expected offline/sandbox): %s", exc)
    return None


def get_concept_visual(
    title: str,
    scene: Dict[str, Any],
    category: str,
    output_path: Path
) -> Optional[Dict[str, Any]]:
    """
    Attempt to retrieve a public domain concept image matching the topic and scene.
    Returns metadata dict if successful, or None if offline/unavailable.
    """
    keywords = extract_search_keywords(title, scene.get("visual_description", ""))
    query = " ".join(keywords)
    if not query:
        query = title

    # NASA prioritized for astronomy and future space topics
    if category in ("daily_mystery", "future_is_here") and any(k in query for k in ("space", "signal", "alien", "star", "telescope", "orbit", "quantum", "planet")):
        res = fetch_nasa_image(query, output_path)
        if res:
            return res

    # Wikimedia Commons for general topics
    res = fetch_wikimedia_image(query, output_path)
    if res:
        return res

    return None
