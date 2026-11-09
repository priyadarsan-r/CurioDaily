"""
Carousel publisher with child slide container polling and parent publishing.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from database.db import Database
from publishing.instagram_client import InstagramClient
from publishing.upload_assets import get_public_media_url

logger = logging.getLogger(__name__)


def publish_carousel_post(
    content_record: Dict[str, Any],
    slide_file_paths: List[str],
    db: Database,
    client: Optional[InstagramClient] = None
) -> Dict[str, Any]:
    content_id = content_record["content_id"]
    client = client or InstagramClient()

    if db.is_content_published(content_id):
        logger.warning("Content %s already published. Skipping duplicate.", content_id)
        return {"success": True, "already_published": True}

    caption = content_record.get("caption", "")

    # 1. Create child containers for each slide
    child_container_ids: List[str] = []
    for idx, slide_path in enumerate(slide_file_paths):
        slide_url = get_public_media_url(slide_path)
        child_id = client.create_image_container(slide_url, caption="", is_carousel_item=True)
        if not child_id:
            return {"success": False, "error": f"Failed creating slide {idx + 1} container"}
        child_container_ids.append(child_id)

    # 2. Create parent carousel container
    parent_id = client.create_carousel_container(child_container_ids, caption)
    if not parent_id:
        return {"success": False, "error": "Failed creating parent carousel container"}

    # 3. Poll parent container
    if not client.poll_container_status(parent_id):
        return {"success": False, "error": f"Carousel container {parent_id} processing failed"}

    # 4. Publish parent container
    media_id = client.publish_container(parent_id)
    if not media_id:
        return {"success": False, "error": "Failed publishing carousel"}

    return {
        "success": True,
        "content_id": content_id,
        "container_id": parent_id,
        "media_id": media_id,
        "slides_count": len(child_container_ids),
    }
