"""
Fetch and parse content from source URLs.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = "CurioDailyResearch/1.0 (Educational Content Verification)"


def fetch_source_text(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Fetch web page, parse with BeautifulSoup, and extract clean main text and metadata.
    """
    headers = {"User-Agent": USER_AGENT}
    result: Dict[str, Any] = {
        "url": url,
        "title": "",
        "text": "",
        "success": False,
        "error": None,
    }

    if not url or not url.startswith("http"):
        result["error"] = "Invalid URL"
        return result

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code}"
            return result

        soup = BeautifulSoup(resp.content, "html.parser")

        # Remove irrelevant elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            element.decompose()

        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text().strip()

        paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 30]
        main_text = "\n\n".join(paragraphs)

        result["title"] = title
        result["text"] = main_text
        result["success"] = True

    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        result["error"] = str(exc)

    return result
