"""
Daily editorial selection orchestrator.
Selects 4 Reels (1 per pillar), 2 single-image feed posts, and 1 carousel
from verified, scored topics.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db import Database
from research.extract_claims import extract_claims
from research.score_topics import score_topic
from research.verify_claims import verify_claims_against_sources

logger = logging.getLogger(__name__)

PILLARS = ["money_secrets", "human_psychology", "future_is_here", "daily_mystery"]


def process_topic_research(db: Database, topic: Dict[str, Any]) -> Dict[str, Any]:
    topic_id = topic["topic_id"]
    sources = db.get_sources_by_topic(topic_id)
    summary = topic.get("summary", "")
    title = topic.get("title", "")

    # Extract claims
    raw_claims = extract_claims(summary, title)
    verification = verify_claims_against_sources(raw_claims, sources)

    # Persist claims
    for claim in verification["verified_claims"]:
        db.insert_claim({
            "topic_id": topic_id,
            "claim_text": claim["claim_text"],
            "supporting_source_ids": claim["supporting_source_ids"],
            "verification_status": "verified",
            "confidence_notes": claim["confidence_notes"],
        })

    for claim in verification["unverified_claims"]:
        db.insert_claim({
            "topic_id": topic_id,
            "claim_text": claim["claim_text"],
            "supporting_source_ids": [],
            "verification_status": "unverified",
            "confidence_notes": claim["confidence_notes"],
        })

    # Score topic
    score_res = score_topic(topic, sources, raw_claims)
    total_score = score_res["total_score"]
    passed = score_res["passed_threshold"] and verification["is_verified"]

    new_status = "scored" if passed else "held"
    db.update_topic_status(topic_id, new_status, score=total_score)

    return {
        "topic_id": topic_id,
        "title": title,
        "category": topic.get("category"),
        "score": total_score,
        "passed": passed,
        "status": new_status,
        "claims_count": len(verification["verified_claims"]),
    }


def make_editorial_selection(db: Database) -> Dict[str, Any]:
    """
    Selects 4 Reels (1 per pillar), 2 image feed posts, and 1 carousel.
    """
    # 1. First, process any newly discovered topics
    discovered = db.get_topics_by_status("discovered")
    for topic in discovered:
        process_topic_research(db, topic)

    scored_topics = db.get_topics_by_status("scored")
    selection: Dict[str, Any] = {
        "reels": {},
        "feed_posts": [],
        "carousel": None,
        "held": [],
    }

    used_topic_ids = set()

    # 1. Select 4 Reels (one per pillar)
    for pillar in PILLARS:
        pillar_candidates = [t for t in scored_topics if t.get("category") == pillar and t["topic_id"] not in used_topic_ids]
        if pillar_candidates:
            chosen = pillar_candidates[0]
            selection["reels"][pillar] = chosen
            used_topic_ids.add(chosen["topic_id"])
            db.update_topic_status(chosen["topic_id"], "selected")
        else:
            logger.warning("No eligible candidate for Reel in pillar: %s", pillar)

    # 2. Select 1 Carousel (from remaining highest scoring topics with good detail)
    remaining = [t for t in scored_topics if t["topic_id"] not in used_topic_ids]
    if remaining:
        carousel_topic = remaining[0]
        selection["carousel"] = carousel_topic
        used_topic_ids.add(carousel_topic["topic_id"])
        db.update_topic_status(carousel_topic["topic_id"], "selected")

    # 3. Select 2 Feed Posts
    remaining = [t for t in scored_topics if t["topic_id"] not in used_topic_ids]
    for _ in range(min(2, len(remaining))):
        post_topic = remaining.pop(0)
        selection["feed_posts"].append(post_topic)
        used_topic_ids.add(post_topic["topic_id"])
        db.update_topic_status(post_topic["topic_id"], "selected")

    return selection


def main() -> None:
    parser = argparse.ArgumentParser(description="Run daily editorial selection")
    parser.add_argument("--db", type=str, default=None, help="Database path")
    args = parser.parse_args()

    db = Database(args.db)
    selection = make_editorial_selection(db)
    print("--- Editorial Selection Summary ---")
    print(f"Reels Selected: {len(selection['reels'])}/4")
    for pillar, topic in selection["reels"].items():
        print(f"  [{pillar}]: {topic['title']} (Score: {topic.get('topic_score')})")
    print(f"Carousel Selected: {selection['carousel']['title'] if selection['carousel'] else 'None'}")
    print(f"Feed Posts Selected: {len(selection['feed_posts'])}/2")
    for p in selection["feed_posts"]:
        print(f"  [Feed]: {p['title']}")


if __name__ == "__main__":
    main()
