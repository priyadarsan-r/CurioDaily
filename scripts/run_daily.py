"""
Master daily orchestration pipeline for CurioDaily.
Executes Discovery -> Research -> Scripting -> Media Production -> Queue -> Publishing -> Insights.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.quality_check import check_script_quality
from ai.script_generator import ScriptGenerator
from ai.storyboard_generator import generate_reel_storyboard
from analytics.fetch_insights import sync_all_published_insights
from database.db import Database
from discovery.collect import collect_all_sources
from media.create_carousel import build_carousel
from media.create_feed_post import build_feed_post
from media.create_reel import build_reel
from publishing.publish_queue import process_queue
from research.editorial_selection import make_editorial_selection
from scripts.export_report import generate_daily_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("CurioDailyDailyRunner")


def run_pipeline(
    stage: str = "all",
    pillar: Optional[str] = None,
    format_type: Optional[str] = None,
    db_path: str = None
) -> Dict[str, Any]:
    db = Database(db_path)
    script_gen = ScriptGenerator()
    results: Dict[str, Any] = {}

    target_pillar = pillar if pillar and pillar != "all" else None
    target_format = format_type if format_type and format_type != "all" else None

    # ---------------------------------------------------------
    # Stage 1: Discovery
    # ---------------------------------------------------------
    if stage in ("all", "discover"):
        logger.info("Starting Stage 1: Topic Discovery")
        disc_stats = collect_all_sources(db, include_seeds=True)
        results["discovery"] = disc_stats
        logger.info("Discovery completed: %s", disc_stats)

    # ---------------------------------------------------------
    # Stage 2: Research & Editorial Selection
    # ---------------------------------------------------------
    if stage in ("all", "research", "generate"):
        logger.info("Starting Stage 2: Research & Editorial Selection")
        editorial = make_editorial_selection(db)
        results["editorial_selection"] = {
            "reels": list(editorial["reels"].keys()),
            "feed_posts": len(editorial["feed_posts"]),
            "carousel": bool(editorial["carousel"]),
        }
        logger.info("Editorial selection completed: 4 Reels, %d Posts, Carousel: %s",
                    len(editorial["feed_posts"]), bool(editorial["carousel"]))

    # ---------------------------------------------------------
    # Stage 3 & 4: Scripting and Media Production
    # ---------------------------------------------------------
    if stage in ("all", "generate"):
        logger.info("Starting Stage 3 & 4: Scripting & Media Production (Pillar: %s, Format: %s)", target_pillar or "all", target_format or "all")
        generated_content = []

        # Reels
        if target_format in (None, "reel"):
            for p, topic in editorial.get("reels", {}).items():
                if target_pillar and p != target_pillar:
                    continue
                topic_id = topic["topic_id"]
                claims = db.get_claims_by_topic(topic_id)
                sources = db.get_sources_by_topic(topic_id)

                reel_script = script_gen.generate_reel_script(topic, claims, sources)
                storyboard = generate_reel_storyboard(reel_script)
                reel_script["storyboard_json"] = storyboard
                reel_script["script"] = reel_script["narration"]

                qa = check_script_quality(reel_script)
                quality_status = "approved" if qa["passed"] else "rejected"

                content_id = db.insert_content({
                    "topic_id": topic_id,
                    "format": "reel",
                    "category": p,
                    "script": reel_script["narration"],
                    "caption": reel_script["caption"],
                    "storyboard_json": storyboard,
                    "quality_status": quality_status,
                })
                reel_script["content_id"] = content_id

                if quality_status == "approved":
                    build_reel(reel_script)
                    db.enqueue_content(content_id, datetime.now(timezone.utc).isoformat())
                    generated_content.append({"content_id": content_id, "format": "reel", "category": p})

        # Feed Posts
        if target_format in (None, "image") and not target_pillar:
            for post_topic in editorial.get("feed_posts", []):
                topic_id = post_topic["topic_id"]
                claims = db.get_claims_by_topic(topic_id)
                sources = db.get_sources_by_topic(topic_id)

                post_script = script_gen.generate_feed_post_script(post_topic, claims, sources)
                qa = check_script_quality(post_script)
                quality_status = "approved" if qa["passed"] else "rejected"

                content_id = db.insert_content({
                    "topic_id": topic_id,
                    "format": "image",
                    "category": post_topic.get("category", "daily_mystery"),
                    "script": post_script["headline"],
                    "caption": post_script["caption"],
                    "quality_status": quality_status,
                })
                post_script["content_id"] = content_id

                if quality_status == "approved":
                    build_feed_post(post_script)
                    db.enqueue_content(content_id, datetime.now(timezone.utc).isoformat())
                    generated_content.append({"content_id": content_id, "format": "image"})

        # Carousel
        if target_format in (None, "carousel") and not target_pillar:
            carousel_topic = editorial.get("carousel")
            if carousel_topic:
                topic_id = carousel_topic["topic_id"]
                claims = db.get_claims_by_topic(topic_id)
                sources = db.get_sources_by_topic(topic_id)

                car_script = script_gen.generate_carousel_script(carousel_topic, claims, sources)
                qa = check_script_quality(car_script)
                quality_status = "approved" if qa["passed"] else "rejected"

                content_id = db.insert_content({
                    "topic_id": topic_id,
                    "format": "carousel",
                    "category": carousel_topic.get("category", "daily_mystery"),
                    "script": carousel_topic["title"],
                    "caption": car_script["caption"],
                    "storyboard_json": car_script["slides"],
                    "quality_status": quality_status,
                })
                car_script["content_id"] = content_id

                if quality_status == "approved":
                    build_carousel(car_script)
                    db.enqueue_content(content_id, datetime.now(timezone.utc).isoformat())
                    generated_content.append({"content_id": content_id, "format": "carousel"})

        results["generated_content"] = generated_content
        logger.info("Generated %d content pieces successfully.", len(generated_content))

    # ---------------------------------------------------------
    # Stage 5: Publishing
    # ---------------------------------------------------------
    if stage in ("all", "publish"):
        logger.info("Starting Stage 5: Publishing Queue Processing")
        pub_stats = process_queue(db)
        results["publishing"] = pub_stats
        logger.info("Publishing completed: %s", pub_stats)

    # ---------------------------------------------------------
    # Stage 6: Insights & Reporting
    # ---------------------------------------------------------
    if stage in ("all", "insights"):
        logger.info("Starting Stage 6: Insights and Reporting")
        synced_count = sync_all_published_insights(db)
        report = generate_daily_report(db)
        results["insights_synced"] = synced_count
        results["report"] = report

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute CurioDaily Daily Engine")
    parser.add_argument("--stage", type=str, default="all", choices=["all", "discover", "research", "generate", "publish", "insights"])
    parser.add_argument("--pillar", type=str, default=None, choices=["money_secrets", "human_psychology", "future_is_here", "daily_mystery", "all"], help="Filter generation by pillar")
    parser.add_argument("--format", type=str, default=None, choices=["reel", "image", "carousel", "all"], help="Filter generation by format")
    parser.add_argument("--db", type=str, default=None, help="Database path")
    args = parser.parse_args()

    results = run_pipeline(stage=args.stage, pillar=args.pillar, format_type=args.format, db_path=args.db)
    print("=== CurioDaily Pipeline Finished Successfully ===")
    print(results)


if __name__ == "__main__":
    main()
