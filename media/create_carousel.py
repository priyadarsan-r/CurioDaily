"""
Multi-slide carousel creation pipeline.
Generates 5-8 matching 1080x1350 vertical slides with progress indicators.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from media.asset_manager import AssetManager
from media.create_visuals import create_carousel_slide_image

logger = logging.getLogger(__name__)


def build_carousel(
    content_record: Dict[str, Any],
    output_dir: Optional[Path] = None,
    asset_mgr: Optional[AssetManager] = None
) -> Dict[str, Any]:
    content_id = content_record.get("content_id", "test_carousel")
    title = content_record.get("title", "")
    category = content_record.get("category", "daily_mystery")
    slides = content_record.get("slides", [])

    asset_mgr = asset_mgr or AssetManager(output_dir)
    content_dir = asset_mgr.get_content_dir(content_id)

    total_slides = len(slides)
    slide_paths: List[str] = []

    # Fetch real photo for cover slide
    raw_photo = content_dir / "raw_cover_photo.jpg"
    if not raw_photo.exists():
        from media.internet_media import fetch_wikimedia_photo_url, download_file
        photo_info = fetch_wikimedia_photo_url(title)
        if photo_info and download_file(photo_info["url"], raw_photo):
            if slides:
                slides[0]["image_path"] = str(raw_photo)
            asset_mgr.record_asset(content_id, raw_photo, "photo", source_url=photo_info["url"], license_name=photo_info["license"], attribution_text=photo_info["title"])
    elif raw_photo.exists() and slides:
        slides[0]["image_path"] = str(raw_photo)

    for idx, slide in enumerate(slides, start=1):
        slide_file = content_dir / f"slide_{idx:02d}.jpg"
        create_carousel_slide_image(
            slide=slide,
            topic_title=title,
            category=category,
            slide_index=idx,
            total_slides=total_slides,
            output_path=slide_file
        )
        slide_paths.append(str(slide_file.resolve()))
        asset_mgr.record_asset(content_id, slide_file, "carousel_slide", attribution_text="CurioDaily Carousel")

    return {
        "content_id": content_id,
        "format": "carousel",
        "slide_paths": slide_paths,
        "slide_count": len(slide_paths),
        "caption": content_record.get("caption", ""),
    }
