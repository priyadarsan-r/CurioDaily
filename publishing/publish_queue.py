"""
Publishing Queue Processor.
Polls pending items, executes publishing workflows, guarantees idempotency,
and logs publication results to SQLite.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from database.db import Database
from publishing.instagram_client import InstagramClient
from publishing.publish_carousel import publish_carousel_post
from publishing.publish_image import publish_image_post
from publishing.publish_reel import publish_reel_post

logger = logging.getLogger(__name__)

PAUSE_FILE = Path(__file__).resolve().parent.parent / "config" / "PAUSE_PUBLISHING"


def is_publishing_paused() -> bool:
    """Check if emergency human kill-switch or pause override is active."""
    if os.getenv("PUBLISHING_PAUSED", "").lower() in ("true", "1", "yes"):
        return True
    if PAUSE_FILE.exists():
        return True
    schedule_file = Path(__file__).resolve().parent.parent / "config" / "schedule.yml"
    if schedule_file.exists():
        try:
            import yaml
            with open(schedule_file, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                if cfg.get("publishing_paused") is True:
                    return True
        except Exception:
            pass
    return False


def set_publishing_pause(paused: bool) -> None:
    """Set or remove emergency pause file."""
    if paused:
        PAUSE_FILE.parent.mkdir(parents=True, exist_ok=True)
        PAUSE_FILE.write_text("PAUSED", encoding="utf-8")
        logger.warning("Emergency kill switch activated: Publishing PAUSED.")
    else:
        if PAUSE_FILE.exists():
            PAUSE_FILE.unlink()
        logger.info("Publishing RESUMED.")


def process_queue(db: Database, client: Optional[InstagramClient] = None) -> Dict[str, Any]:
    client = client or InstagramClient()
    now_iso = datetime.now(timezone.utc).isoformat()
    pending_items = db.get_pending_queue(before_time=now_iso)

    if is_publishing_paused():
        logger.warning("Publishing is paused via human override / kill switch. No content will be published.")
        return {
            "processed": 0,
            "published": 0,
            "failed": 0,
            "skipped": len(pending_items),
            "paused": True,
        }

    stats = {
        "processed": 0,
        "published": 0,
        "failed": 0,
        "skipped": 0,
        "paused": False,
    }

    for item in pending_items:
        queue_id = item["queue_id"]
        content_id = item["content_id"]
        format_type = item.get("format", "reel")
        manifest = item.get("asset_manifest_json", [])

        # Check if already published
        if db.is_content_published(content_id):
            db.update_queue_item(queue_id, status="published")
            stats["skipped"] += 1
            continue

        stats["processed"] += 1
        result: Dict[str, Any] = {"success": False}

        # Resolve asset paths from manifest or default folder
        content_dir = Path(__file__).resolve().parent.parent / "output" / content_id

        if format_type == "reel":
            video_file = content_dir / "reel.mp4"
            result = publish_reel_post(item, str(video_file), db, client)

        elif format_type == "image":
            img_file = content_dir / "feed_post.jpg"
            result = publish_image_post(item, str(img_file), db, client)

        elif format_type == "carousel":
            slide_files = sorted(list(content_dir.glob("slide_*.jpg")))
            slide_paths = [str(f.resolve()) for f in slide_files]
            if not slide_paths:
                result = {"success": False, "error": "No carousel slides found on disk"}
            else:
                result = publish_carousel_post(item, slide_paths, db, client)

        if result.get("success"):
            stats["published"] += 1
            db.update_queue_item(
                queue_id=queue_id,
                status="published",
                container_id=result.get("container_id"),
                media_id=result.get("media_id"),
                published_at=datetime.now(timezone.utc).isoformat()
            )
            logger.info("Successfully published %s (Content ID: %s)", format_type, content_id)
        else:
            stats["failed"] += 1
            err_msg = result.get("error", "Unknown error")
            db.update_queue_item(
                queue_id=queue_id,
                status="failed",
                attempt_increment=True,
                last_error=err_msg
            )
            logger.error("Failed publishing %s (Content ID: %s): %s", format_type, content_id, err_msg)

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Process pending publishing queue")
    parser.add_argument("--db", type=str, default=None, help="Database path")
    args = parser.parse_args()

    db = Database(args.db)
    stats = process_queue(db)
    print(f"Queue Processing Finished: Processed {stats['processed']}, Published {stats['published']}, Failed {stats['failed']}")


if __name__ == "__main__":
    main()
