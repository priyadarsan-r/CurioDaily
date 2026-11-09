"""
Reel publisher with idempotency checks and container status polling.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from database.db import Database
from publishing.instagram_client import InstagramClient
from publishing.upload_assets import get_public_media_url

logger = logging.getLogger(__name__)


def publish_reel_post(
    content_record: Dict[str, Any],
    video_file_path: str,
    db: Database,
    client: Optional[InstagramClient] = None
) -> Dict[str, Any]:
    content_id = content_record["content_id"]
    client = client or InstagramClient()

    # Idempotency check: don't publish if already published
    if db.is_content_published(content_id):
        logger.warning("Content %s already published. Skipping duplicate.", content_id)
        return {"success": True, "already_published": True}

    caption = content_record.get("caption", "")
    video_url = get_public_media_url(video_file_path)

    # 1. Create container
    container_id = client.create_reel_container(video_url, caption)
    if not container_id:
        return {"success": False, "error": "Failed creating reel container"}

    # 2. Poll container status
    if not client.poll_container_status(container_id):
        return {"success": False, "error": f"Container {container_id} processing failed"}

    # 3. Publish container
    media_id = client.publish_container(container_id)
    if not media_id:
        return {"success": False, "error": "Failed publishing reel"}

    return {
        "success": True,
        "content_id": content_id,
        "container_id": container_id,
        "media_id": media_id,
    }
