"""
Image Providers: Pollinations AI, Wikimedia Commons, NASA, and Pexels.
"""

from __future__ import annotations

import logging
import os
import urllib.parse
from pathlib import Path
from typing import Any, Dict, Optional
from PIL import Image
import requests

from media.providers.base import ImageProvider

logger = logging.getLogger(__name__)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
WIKI_HEADERS = {"User-Agent": "CurioDailyBot/1.0 (Educational Content Engine; contact@curiodaily.org)"}


def download_image_file(url: str, dest_path: Path, timeout: float = 15.0) -> bool:
    """Download and validate an image file."""
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        if resp.status_code == 200 and len(resp.content) > 5000:
            with open(dest_path, "wb") as f:
                f.write(resp.content)
            # Validate Pillow can open it
            with Image.open(dest_path) as im:
                im.verify()
            return True
    except Exception as exc:
        logger.debug(f"Failed image download from {url}: {exc}")
        if dest_path.exists():
            dest_path.unlink()
    return False


class PollinationsImageProvider(ImageProvider):
    """Free AI Image Generation via Pollinations."""

    @property
    def name(self) -> str:
        return "pollinations_ai"

    def is_available(self) -> bool:
        return True

    def fetch_image(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str = "9:16",
        keywords: Optional[str] = None
    ) -> bool:
        clean_prompt = urllib.parse.quote(prompt[:140])
        # Vertical 720x1280 (scaled up to 1080x1920 with lanczos)
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=720&height=1280&nologo=true"
        return download_image_file(url, output_path, timeout=25.0)


class WikimediaImageProvider(ImageProvider):
    """High-resolution verified public domain real photography from Wikimedia Commons."""

    @property
    def name(self) -> str:
        return "wikimedia_commons"

    def is_available(self) -> bool:
        return True

    def fetch_image(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str = "9:16",
        keywords: Optional[str] = None
    ) -> bool:
        query = keywords or prompt[:40]
        url = (
            f"https://en.wikipedia.org/w/api.php?action=query&format=json&generator=search"
            f"&gsrsearch={urllib.parse.quote(query)}&gsrlimit=3&prop=pageimages&pithumbsize=1280"
        )
        try:
            resp = requests.get(url, headers=WIKI_HEADERS, timeout=6.0)
            if resp.status_code == 200:
                pages = resp.json().get("query", {}).get("pages", {})
                for _, p in pages.items():
                    thumb = p.get("thumbnail", {}).get("source")
                    if thumb and not thumb.endswith(".svg.png"):
                        if download_image_file(thumb, output_path):
                            return True
        except Exception as exc:
            logger.debug(f"Wikimedia search error for {query}: {exc}")
        return False


class NASAImageProvider(ImageProvider):
    """NASA Images API for scientific, planetary, and space subjects."""

    @property
    def name(self) -> str:
        return "nasa_archives"

    def is_available(self) -> bool:
        return True

    def fetch_image(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str = "9:16",
        keywords: Optional[str] = None
    ) -> bool:
        query = keywords or prompt[:35]
        url = f"https://images-api.nasa.gov/search?q={urllib.parse.quote(query)}&media_type=image"
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=8.0)
            if resp.status_code == 200:
                items = resp.json().get("collection", {}).get("items", [])
                if items:
                    links = items[0].get("links", [])
                    if links and links[0].get("href"):
                        return download_image_file(links[0]["href"], output_path)
        except Exception as exc:
            logger.debug(f"NASA search error for {query}: {exc}")
        return False


class PexelsImageProvider(ImageProvider):
    """Pexels API curated high-resolution photography."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PEXELS_API_KEY", "")

    @property
    def name(self) -> str:
        return "pexels_photos"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def fetch_image(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str = "9:16",
        keywords: Optional[str] = None
    ) -> bool:
        if not self.is_available():
            return False

        query = keywords or prompt[:35]
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=3"
        try:
            resp = requests.get(url, headers={"Authorization": self.api_key, "User-Agent": USER_AGENT}, timeout=8.0)
            if resp.status_code == 200:
                photos = resp.json().get("photos", [])
                if photos and photos[0].get("src", {}).get("large2x"):
                    img_url = photos[0]["src"]["large2x"]
                    return download_image_file(img_url, output_path)
        except Exception as exc:
            logger.debug(f"Pexels photo search error: {exc}")
        return False
