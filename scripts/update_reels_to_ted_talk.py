"""
Regenerate all Reel scripts using TED-talk storytelling style,
update content records in the database, and re-render the reels.
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

from ai.quality_check import check_script_quality
from ai.script_generator import ScriptGenerator
from ai.storyboard_generator import generate_reel_storyboard
from media.asset_manager import AssetManager
from media.create_reel import build_reel
from media.tts import TTSManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TEDTalkReels")

DB_PATH = PROJECT_ROOT / "database" / "content_engine.db"
OUTPUT_DIR = PROJECT_ROOT / "output"


def update_and_rebuild_ted_talk_reels():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.content_id, c.topic_id, c.category, t.title, t.summary
        FROM content c
        JOIN topics t ON c.topic_id = t.topic_id
        WHERE c.format = 'reel'
    """)
    rows = cursor.fetchall()

    script_gen = ScriptGenerator()
    asset_mgr = AssetManager(OUTPUT_DIR)
    tts_mgr = TTSManager()

    logger.info(f"Updating {len(rows)} reels to TED-talk storytelling style...")

    for r in rows:
        cid, tid, cat, title, summary = r
        topic = {"topic_id": tid, "title": title, "category": cat, "summary": summary}

        cursor.execute("SELECT claim_text, verification_status FROM claims WHERE topic_id = ?", (tid,))
        claims = [{"claim_text": row[0], "verification_status": row[1]} for row in cursor.fetchall()]

        cursor.execute("SELECT url FROM sources WHERE topic_id = ?", (tid,))
        sources = [{"url": row[0]} for row in cursor.fetchall()]

        # Generate TED-talk style script
        ted_script = script_gen.generate_reel_script(topic, claims, sources)
        storyboard = generate_reel_storyboard(ted_script)
        ted_script["storyboard_json"] = storyboard
        ted_script["content_id"] = cid

        # Quality check
        qa = check_script_quality(ted_script)
        logger.info(f"Quality Check for [{cat.upper()}] '{title}': Passed={qa['passed']}")

        # Update database
        cursor.execute("""
            UPDATE content
            SET script = ?, caption = ?, storyboard_json = ?
            WHERE content_id = ?
        """, (
            ted_script["narration"],
            ted_script["caption"],
            json.dumps(storyboard),
            cid
        ))
        conn.commit()

        # Clean old scene clips and audios
        content_dir = asset_mgr.get_content_dir(cid)
        for pattern in ("scene_*", "*.srt", "narration.wav", "reel.mp4"):
            for old_f in content_dir.glob(pattern):
                try:
                    old_f.unlink()
                except Exception:
                    pass

        # Build Reel
        logger.info(f"\n---> Building TED-talk Reel: [{cat.upper()}] '{title}'")
        logger.info(f"Hook: \"{ted_script['hook']}\"")
        res = build_reel(
            content_record=ted_script,
            output_dir=OUTPUT_DIR,
            asset_mgr=asset_mgr,
            tts_mgr=tts_mgr
        )
        mp4_path = Path(res["video_path"])
        size_bytes = mp4_path.stat().st_size if mp4_path.exists() else 0
        logger.info(f"Rebuilt MP4: {mp4_path} ({size_bytes:,} bytes, {res['duration_sec']}s)")

    conn.close()
    logger.info("\nAll TED-talk Reels updated and rendered successfully!")


if __name__ == "__main__":
    update_and_rebuild_ted_talk_reels()
