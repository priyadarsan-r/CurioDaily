"""
Single image feed post publisher with idempotency checks.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from database.db import Database
from publishing.instagram_client import InstagramClient
from publishing.upload_assets import get_public_media_url

logger = logging.getLogger(__name__)


def publish_image_post(
    content_record: Dict[str, Any],
    image_file_path: str,
    db: Database,
    client: Optional[InstagramClient] = None
) -> Dict[str, Any]:
    content_id = content_record["content_id"]
    client = client or InstagramClient()

    if db.is_content_published(content_id):
        logger.warning("Content %s already published. Skipping duplicate.", content_id)
        return {"success": True, "already_published": True}

    caption = content_record.get("caption", "")
    image_url = get_public_media_url(image_file_path)

    # 1. Create image container
    container_id = client.create_image_container(image_url, caption)
    if not container_id:
        return {"success": False, "error": "Failed creating image container"}

    # 2. Publish container
    media_id = client.publish_container(container_id)
    if not media_id:
        return {"success": False, "error": "Failed publishing image"}

    return {
        "success": True,
        "content_id": content_id,
        "container_id": container_id,
        "media_id": media_id,
    }
