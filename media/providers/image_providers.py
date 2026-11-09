"""
Image Providers: Pollinations AI, Wikimedia Commons, NASA, and Pexels.
"""

from __future__ import annotations

import logging
import os
import re
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image
import requests

from media.providers.base import ImageProvider

logger = logging.getLogger(__name__)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
WIKI_HEADERS = {"User-Agent": "CurioDailyBot/1.0 (Educational Content Engine; contact@curiodaily.org)"}


def crop_and_resize_to_vertical(image_path: Path, width: int = 1080, height: int = 1920) -> bool:
    """Scale and center-crop any image to vertical 9:16 (default 1080x1920) using Lanczos."""
    try:
        with Image.open(image_path) as im:
            im_rgb = im.convert("RGB")
            if im_rgb.size == (width, height):
                return True
            ratio = max(width / im_rgb.width, height / im_rgb.height)
            new_size = (int(round(im_rgb.width * ratio)), int(round(im_rgb.height * ratio)))
            resized = im_rgb.resize(new_size, Image.Resampling.LANCZOS)
            left = (resized.width - width) // 2
            top = (resized.height - height) // 2
            cropped = resized.crop((left, top, left + width, top + height))
            cropped.save(str(image_path), "JPEG", quality=95)
            return True
    except Exception as exc:
        logger.debug("Failed crop_and_resize_to_vertical on %s: %s", image_path, exc)
        return False


def extract_clean_search_query(
    prompt: str,
    keywords: Optional[str] = None,
    visual_desc: Optional[str] = None
) -> str:
    """
    Extract high-precision, distinct search keywords from prompt/keywords/visual_desc,
    stripping camera jargon, lens directions, and prompt boilerplate.
    """
    if keywords and len(keywords.strip()) > 2:
        clean_kw = re.sub(r"[^a-zA-Z0-9\s]", " ", keywords).strip()
        words = clean_kw.split()
        if words:
            return " ".join(words[:4])

    source = visual_desc or prompt
    # Strip camera instructions, lenses, resolutions, aspect ratios
    jargon = [
        r"award-winning", r"35mm film photograph", r"35mm", r"cinematic documentary", r"cinematic",
        r"ultra-photorealistic", r"photorealistic", r"vertical 9:16", r"9:16", r"panavision",
        r"anamorphic", r"shallow depth of field", r"depth of field", r"shallow focus",
        r"natural lighting", r"dramatic lighting", r"golden hour", r"8k resolution", r"8k",
        r"shot on", r"f/1\.8", r"no text", r"no captions", r"no watermark", r"no diagrams",
        r"no charts", r"authentic textures", r"medium shot of", r"close-up shot of",
        r"wide shot of", r"tracking shot of", r"low angle shot of", r"low-angle",
        r"medium two-shot", r"medium shot", r"establishing shot", r"pure real-world",
        r"real world", r"real-world", r"ultra-realistic", r"film photograph", r"photograph"
    ]
    cleaned = source
    for pattern in jargon:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", cleaned)
    stopwords = {
        "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "with", "of",
        "by", "from", "how", "why", "what", "is", "are", "this", "that", "scene",
        "card", "graphic", "visual", "showing", "clean", "high", "contrast", "shot",
        "angle", "camera", "lighting", "detailed", "about", "your", "they", "which",
        "when", "there", "their", "into", "over", "after", "two", "one"
    }
    words = [w for w in cleaned.split() if len(w) > 2 and w.lower() not in stopwords]
    if words:
        return " ".join(words[:4])
    return prompt[:30].strip()


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
            crop_and_resize_to_vertical(dest_path)
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
    """High-resolution verified public domain real photography from Wikimedia Commons with strict deduplication."""

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
        keywords: Optional[str] = None,
        registry: Optional[Any] = None,
        visual_desc: Optional[str] = None,
        **kwargs: Any
    ) -> bool:
        query = extract_clean_search_query(prompt, keywords=keywords, visual_desc=visual_desc)
        url = (
            f"https://en.wikipedia.org/w/api.php?action=query&format=json&generator=search"
            f"&gsrsearch={urllib.parse.quote(query)}&gsrlimit=10&prop=pageimages&pithumbsize=1280"
        )
        try:
            resp = requests.get(url, headers=WIKI_HEADERS, timeout=7.0)
            if resp.status_code == 200:
                pages = resp.json().get("query", {}).get("pages", {})
                for _, p in pages.items():
                    thumb = p.get("thumbnail", {}).get("source")
                    if not thumb or thumb.endswith(".svg.png"):
                        continue
                    if registry and hasattr(registry, "is_url_used") and registry.is_url_used(thumb):
                        continue
                    if download_image_file(thumb, output_path):
                        if registry and hasattr(registry, "is_hash_used") and registry.is_hash_used(output_path):
                            output_path.unlink(missing_ok=True)
                            continue
                        if registry and hasattr(registry, "used_urls"):
                            clean_u = thumb.split("?")[0].lower()
                            registry.used_urls.add(clean_u)
                        return True
        except Exception as exc:
            logger.debug(f"Wikimedia search error for {query}: {exc}")
        return False


class NASAImageProvider(ImageProvider):
    """NASA Images API for scientific, planetary, and space subjects with strict deduplication."""

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
        keywords: Optional[str] = None,
        registry: Optional[Any] = None,
        visual_desc: Optional[str] = None,
        **kwargs: Any
    ) -> bool:
        query = extract_clean_search_query(prompt, keywords=keywords, visual_desc=visual_desc)
        url = f"https://images-api.nasa.gov/search?q={urllib.parse.quote(query)}&media_type=image"
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=8.0)
            if resp.status_code == 200:
                items = resp.json().get("collection", {}).get("items", [])
                for item in items[:8]:
                    links = item.get("links", [])
                    if links and links[0].get("href"):
                        href = links[0]["href"]
                        if registry and hasattr(registry, "is_url_used") and registry.is_url_used(href):
                            continue
                        if download_image_file(href, output_path):
                            if registry and hasattr(registry, "is_hash_used") and registry.is_hash_used(output_path):
                                output_path.unlink(missing_ok=True)
                                continue
                            if registry and hasattr(registry, "used_urls"):
                                clean_u = href.split("?")[0].lower()
                                registry.used_urls.add(clean_u)
                            return True
        except Exception as exc:
            logger.debug(f"NASA search error for {query}: {exc}")
        return False


class PexelsImageProvider(ImageProvider):
    """Pexels API curated high-resolution photography with strict deduplication."""

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
        keywords: Optional[str] = None,
        registry: Optional[Any] = None,
        visual_desc: Optional[str] = None,
        **kwargs: Any
    ) -> bool:
        if not self.is_available():
            return False

        query = extract_clean_search_query(prompt, keywords=keywords, visual_desc=visual_desc)
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=6"
        try:
            resp = requests.get(url, headers={"Authorization": self.api_key, "User-Agent": USER_AGENT}, timeout=8.0)
            if resp.status_code == 200:
                photos = resp.json().get("photos", [])
                for ph in photos:
                    img_url = ph.get("src", {}).get("large2x")
                    if not img_url:
                        continue
                    if registry and hasattr(registry, "is_url_used") and registry.is_url_used(img_url):
                        continue
                    if download_image_file(img_url, output_path):
                        if registry and hasattr(registry, "is_hash_used") and registry.is_hash_used(output_path):
                            output_path.unlink(missing_ok=True)
                            continue
                        if registry and hasattr(registry, "used_urls"):
                            clean_u = img_url.split("?")[0].lower()
                            registry.used_urls.add(clean_u)
                        return True
        except Exception as exc:
            logger.debug(f"Pexels photo search error: {exc}")
        return False
