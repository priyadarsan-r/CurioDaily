"""
Rebuild all Reels in the content engine with concept-aligned visuals
and compact, sleek subtitle styling.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from media.asset_manager import AssetManager
from media.create_reel import build_reel
from media.tts import TTSManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RebuildReels")

DB_PATH = PROJECT_ROOT / "database" / "content_engine.db"
OUTPUT_DIR = PROJECT_ROOT / "output"


def rebuild_all_reels():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.content_id, c.topic_id, c.format, c.category, c.script, c.storyboard_json, t.title
        FROM content c
        JOIN topics t ON c.topic_id = t.topic_id
        WHERE c.format = 'reel'
    """)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        logger.warning("No reels found in DB content table. Rebuilding pilot reels from output directories.")
        # If no DB rows, check output directories
        return

    logger.info(f"Found {len(rows)} reels to rebuild with concept visuals & smaller subtitles.")
    asset_mgr = AssetManager(OUTPUT_DIR)
    tts_mgr = TTSManager()

    rebuilt = []
    for r in rows:
        cid, tid, fmt, cat, script, sb_json, title = r
        storyboard = json.loads(sb_json) if sb_json else []
        content_record = {
            "content_id": cid,
            "topic_id": tid,
            "format": fmt,
            "category": cat,
            "title": title,
            "script": script,
            "narration": script,
            "storyboard_json": storyboard,
        }

        logger.info(f"\n---> Rebuilding Reel: [{cat.upper()}] '{title}' (ID: {cid})")
        # Clean old scene clips, audios, and srt/ass to ensure fresh rendering and perfect sync
        content_dir = asset_mgr.get_content_dir(cid)
        for pattern in ("scene_*", "*.srt", "*.ass", "narration.wav", "reel.mp4"):
            for old_f in content_dir.glob(pattern):
                try:
                    old_f.unlink()
                except Exception:
                    pass

        res = build_reel(
            content_record=content_record,
            output_dir=OUTPUT_DIR,
            asset_mgr=asset_mgr,
            tts_mgr=tts_mgr
        )

        # Update DB with synced storyboard
        try:
            up_conn = sqlite3.connect(str(DB_PATH))
            up_cur = up_conn.cursor()
            up_cur.execute("UPDATE content SET storyboard_json = ? WHERE content_id = ?", (json.dumps(storyboard), cid))
            up_conn.commit()
            up_conn.close()
        except Exception as e:
            logger.warning(f"Failed to update storyboard in DB: {e}")

        mp4_path = Path(res["video_path"])
        mp4_size = mp4_path.stat().st_size if mp4_path.exists() else 0
        logger.info(f"Rebuilt MP4: {mp4_path} ({mp4_size:,} bytes, {res['duration_sec']}s)")
        rebuilt.append({
            "content_id": cid,
            "category": cat,
            "title": title,
            "video_path": str(mp4_path),
            "size_bytes": mp4_size,
            "scenes": res["scene_count"]
        })

    logger.info(f"\nSuccessfully rebuilt {len(rebuilt)} reels with concept visuals and small subtitles!")
    return rebuilt


if __name__ == "__main__":
    rebuild_all_reels()
