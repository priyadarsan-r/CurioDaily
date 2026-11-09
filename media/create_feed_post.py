"""
Single-image feed post creation pipeline.
Generates 1080x1350 vertical high-resolution graphic.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from media.asset_manager import AssetManager
from media.create_visuals import create_feed_post_image
from media.internet_media import fetch_wikimedia_photo_url, download_file

logger = logging.getLogger(__name__)


def build_feed_post(
    content_record: Dict[str, Any],
    output_dir: Optional[Path] = None,
    asset_mgr: Optional[AssetManager] = None
) -> Dict[str, Any]:
    content_id = content_record.get("content_id", "test_post")
    asset_mgr = asset_mgr or AssetManager(output_dir)
    content_dir = asset_mgr.get_content_dir(content_id)

    image_path = content_dir / "feed_post.jpg"
    create_feed_post_image(content_record, image_path)
    asset_mgr.record_asset(content_id, image_path, "image", attribution_text="CurioDaily Feed Post")

    return {
        "content_id": content_id,
        "format": "image",
        "image_path": str(image_path.resolve()),
        "caption": content_record.get("caption", ""),
    }
