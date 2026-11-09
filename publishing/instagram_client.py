"""
Official Meta Instagram Graph API client.
Handles media containers, carousel containers, status polling, and publishing.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


class InstagramClient:
    def __init__(
        self,
        account_id: Optional[str] = None,
        access_token: Optional[str] = None,
        timeout: int = 30
    ):
        self.account_id = account_id or os.getenv("INSTAGRAM_ACCOUNT_ID")
        self.access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.timeout = timeout
        self.is_configured = bool(self.account_id and self.access_token)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    # -------------------------------------------------------------
    # 1. Container Creation
    # -------------------------------------------------------------
    def create_reel_container(self, video_url: str, caption: str) -> Optional[str]:
        """Create media container for an Instagram Reel."""
        if not self.is_configured:
            logger.info("Instagram client running in mock mode (no credentials configured).")
            return f"mock_container_reel_{int(time.time())}"

        url = f"{GRAPH_API_BASE}/{self.account_id}/media"
        payload = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": True,
        }
        resp = requests.post(url, headers=self._get_headers(), json=payload, timeout=self.timeout)
        if resp.status_code == 200:
            return resp.json().get("id")
        logger.error("Failed creating Reel container: %s", resp.text)
        return None

    def create_image_container(self, image_url: str, caption: str, is_carousel_item: bool = False) -> Optional[str]:
        """Create media container for a single image or a carousel child slide."""
        if not self.is_configured:
            logger.info("Instagram client running in mock mode.")
            return f"mock_container_img_{int(time.time())}"

        url = f"{GRAPH_API_BASE}/{self.account_id}/media"
        payload: Dict[str, Any] = {"image_url": image_url}
        if is_carousel_item:
            payload["is_carousel_item"] = True
        else:
            payload["caption"] = caption

        resp = requests.post(url, headers=self._get_headers(), json=payload, timeout=self.timeout)
        if resp.status_code == 200:
            return resp.json().get("id")
        logger.error("Failed creating Image container: %s", resp.text)
        return None

    def create_carousel_container(self, children_ids: List[str], caption: str) -> Optional[str]:
        """Create parent container for multi-slide Carousel."""
        if not self.is_configured:
            logger.info("Instagram client running in mock mode.")
            return f"mock_container_carousel_{int(time.time())}"

        url = f"{GRAPH_API_BASE}/{self.account_id}/media"
        payload = {
            "media_type": "CAROUSEL",
            "children": children_ids,
            "caption": caption,
        }
        resp = requests.post(url, headers=self._get_headers(), json=payload, timeout=self.timeout)
        if resp.status_code == 200:
            return resp.json().get("id")
        logger.error("Failed creating Carousel container: %s", resp.text)
        return None

    # -------------------------------------------------------------
    # 2. Container Status Polling
    # -------------------------------------------------------------
    def poll_container_status(
        self,
        container_id: str,
        max_attempts: int = 15,
        delay_sec: int = 5
    ) -> bool:
        """Poll container status until FINISHED or ERROR."""
        if not self.is_configured or container_id.startswith("mock_"):
            return True

        url = f"{GRAPH_API_BASE}/{container_id}"
        params = {"fields": "status_code,status"}

        for attempt in range(max_attempts):
            resp = requests.get(url, headers=self._get_headers(), params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                status_code = data.get("status_code")
                if status_code == "FINISHED":
                    return True
                elif status_code in ("ERROR", "EXPIRED"):
                    logger.error("Container %s failed with status: %s", container_id, data.get("status"))
                    return False
            time.sleep(delay_sec)

        logger.warning("Polling timed out for container %s", container_id)
        return False

    # -------------------------------------------------------------
    # 3. Publish Media
    # -------------------------------------------------------------
    def publish_container(self, container_id: str) -> Optional[str]:
        """Publish an approved, ready media container."""
        if not self.is_configured or container_id.startswith("mock_"):
            logger.info("Mock publishing container %s", container_id)
            return f"mock_media_id_{int(time.time())}"

        url = f"{GRAPH_API_BASE}/{self.account_id}/media_publish"
        payload = {"creation_id": container_id}
        resp = requests.post(url, headers=self._get_headers(), json=payload, timeout=self.timeout)
        if resp.status_code == 200:
            return resp.json().get("id")
        logger.error("Failed publishing container %s: %s", container_id, resp.text)
        return None
