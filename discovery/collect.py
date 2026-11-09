"""
Central discovery collector for CurioDaily content engine.
Collects topics from multiple free public sources, deduplicates against SQLite,
and registers new candidates for research.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db import Database
from discovery.google_trends import fetch_google_trends
from discovery.nasa import fetch_nasa_news
from discovery.reddit import fetch_reddit_topics
from discovery.rss_sources import fetch_rss_feed
from discovery.wikipedia import fetch_wikipedia_curiosities

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

# Seed topics to ensure the engine always has high quality educational topics
# available even when offline or when external endpoints are unreachable.
FALLBACK_SEEDS = [
    {
        "title": "The Rule of 72: How Fast Your Money Doubles",
        "summary": "The Rule of 72 is a simple mathematical shortcut used to estimate the number of years required to double your investment at a fixed annual rate of return.",
        "category": "money_secrets",
        "source_url": "https://www.investopedia.com/terms/r/ruleof72.asp",
        "source_type": "seed",
        "publisher": "Investopedia",
    },
    {
        "title": "The Framing Effect: How Choices Are Manipulated",
        "summary": "Cognitive bias where people decide on options based on whether the options are presented with positive or negative connotations; e.g. as a loss or as a gain.",
        "category": "human_psychology",
        "source_url": "https://www.apa.org/topics/cognitive-bias",
        "source_type": "seed",
        "publisher": "American Psychological Association",
    },
    {
        "title": "Solid-State Batteries: The Next Leap in Clean Energy",
        "summary": "Solid-state batteries replace liquid electrolytes with solid ceramics or polymers, promising 2x energy density, faster charging, and zero fire risk for electric vehicles.",
        "category": "future_is_here",
        "source_url": "https://www.nature.com/articles/s41560-020-0575-z",
        "source_type": "seed",
        "publisher": "Nature Energy",
    },
    {
        "title": "The Richat Structure: The Mysterious Eye of the Sahara",
        "summary": "A prominent circular geological feature in the Sahara Desert measuring 40 kilometers across, resembling an impact crater but formed through deeply eroded volcanic dome uplift.",
        "category": "daily_mystery",
        "source_url": "https://earthobservatory.nasa.gov/images/92071/richat-structure",
        "source_type": "seed",
        "publisher": "NASA Earth Observatory",
    },
    # Additional evergreen seed topics for all 4 pillars
    {
        "title": "The Cost of Waiting: The Compounding Gap Between Your 20s and 30s",
        "summary": "Starting an investment portfolio at age 25 versus age 35 can cut final retirement wealth in half even if you contribute double the monthly amount later.",
        "category": "money_secrets",
        "source_url": "https://www.fidelity.com/learning-center/smart-money/compound-interest",
        "source_type": "seed",
        "publisher": "Fidelity Research",
    },
    {
        "title": "The Sunk Cost Fallacy: Why Walking Away Makes You Richer",
        "summary": "Continuing an unprofitable endeavor merely because you have already invested resources into it drains capital that could be redeployed into high-yield opportunities.",
        "category": "money_secrets",
        "source_url": "https://thedecisionlab.com/biases/the-sunk-cost-fallacy",
        "source_type": "seed",
        "publisher": "The Decision Lab",
    },
    {
        "title": "The Dunning-Kruger Effect: Why Incompetence Breeds Supreme Confidence",
        "summary": "People with low expertise in a domain drastically overestimate their competence because they lack the meta-cognitive ability to recognize their own errors.",
        "category": "human_psychology",
        "source_url": "https://psychology.ucdavis.edu/dunning-kruger",
        "source_type": "seed",
        "publisher": "UC Davis Psychology",
    },
    {
        "title": "The Paradox of Choice: Why Abundant Options Paralyze Us",
        "summary": "When faced with dozens of choices, consumers experience decision fatigue, higher regret, and lower satisfaction than when evaluating a curated set of three.",
        "category": "human_psychology",
        "source_url": "https://www.scientificamerican.com/article/the-tyranny-of-choice",
        "source_type": "seed",
        "publisher": "Scientific American",
    },
    {
        "title": "Nuclear Fusion Ignition: Generating Net Energy in the Lab",
        "summary": "National Ignition Facility researchers achieved scientific energy breakeven using high-energy lasers to fuse hydrogen isotopes into helium, releasing net power.",
        "category": "future_is_here",
        "source_url": "https://www.llnl.gov/article/49301/fusion-energy-breakthrough",
        "source_type": "seed",
        "publisher": "Lawrence Livermore National Laboratory",
    },
    {
        "title": "Neuromorphic Computing: Microchips That Think Like Biological Brains",
        "summary": "Brain-inspired silicon processors transmit sparse electrical spikes instead of clock cycles, reducing artificial intelligence energy consumption by 100 times.",
        "category": "future_is_here",
        "source_url": "https://www.nature.com/articles/s41586-019-1424-8",
        "source_type": "seed",
        "publisher": "Nature",
    },
    {
        "title": "The Wow! Signal: The 72-Second Deep Space Cosmic Anomaly",
        "summary": "In 1977, the Big Ear radio telescope detected an intense narrow-band radio signal at the hydrogen line frequency of 1420 MHz that was never detected again.",
        "category": "daily_mystery",
        "source_url": "https://www.planetary.org/articles/the-wow-signal",
        "source_type": "seed",
        "publisher": "The Planetary Society",
    },
    {
        "title": "The Antikythera Mechanism: A 2000-Year-Old Astronomical Computer",
        "summary": "Recovered from a Roman shipwreck off the Greek coast, this intricate bronze geared clockwork accurately calculated solar, lunar, and planetary eclipses.",
        "category": "daily_mystery",
        "source_url": "https://www.nature.com/articles/s41598-021-84310-w",
        "source_type": "seed",
        "publisher": "Nature Scientific Reports",
    },
]


def load_yaml_config(file_name: str) -> Dict[str, Any]:
    file_path = CONFIG_DIR / file_name
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def collect_all_sources(db: Database, include_seeds: bool = True) -> Dict[str, int]:
    sources_cfg = load_yaml_config("sources.yml").get("sources", {})
    all_candidates: List[Dict[str, Any]] = []

    # 1. RSS Feeds
    for rss_item in sources_cfg.get("rss", []):
        url = rss_item.get("url")
        cat = rss_item.get("category", "future_is_here")
        name = rss_item.get("name", "RSS Source")
        if url:
            candidates = fetch_rss_feed(url, category=cat, source_name=name)
            all_candidates.extend(candidates)

    # 2. Reddit Feeds
    for r_item in sources_cfg.get("reddit", []):
        sub = r_item.get("subreddit")
        cat = r_item.get("category", "daily_mystery")
        limit = r_item.get("limit", 10)
        if sub:
            candidates = fetch_reddit_topics(sub, category=cat, limit=limit)
            all_candidates.extend(candidates)

    # 3. Google Trends
    for trend_item in sources_cfg.get("google_trends", {}).get("categories", []):
        cat = trend_item.get("category", "money_secrets")
        candidates = fetch_google_trends(category=cat, limit=5)
        all_candidates.extend(candidates)

    # 4. NASA
    nasa_candidates = fetch_nasa_news(limit=5)
    all_candidates.extend(nasa_candidates)

    # 5. Wikipedia Curiosities
    wiki_candidates = fetch_wikipedia_curiosities(limit=3)
    all_candidates.extend(wiki_candidates)

    # 6. Fallback Seeds
    if include_seeds or len(all_candidates) < 4:
        all_candidates.extend(FALLBACK_SEEDS)

    logger.info("Total raw candidates collected: %d", len(all_candidates))

    # Process deduplication and database persistence
    stats: Dict[str, int] = {
        "discovered": 0,
        "duplicates_skipped": 0,
        "by_pillar": {},
    }

    for candidate in all_candidates:
        title = candidate.get("title", "").strip()
        summary = candidate.get("summary", "").strip()
        category = candidate.get("category", "daily_mystery")

        if not title:
            continue

        if db.check_duplicate_topic(title, summary, lookback_days=30):
            stats["duplicates_skipped"] += 1
            continue

        topic_id = db.insert_topic({
            "title": title,
            "summary": summary,
            "category": category,
            "source_url": candidate.get("source_url", ""),
            "source_type": candidate.get("source_type", "rss"),
            "status": "discovered",
        })

        # Record initial source
        if candidate.get("source_url"):
            db.insert_source({
                "topic_id": topic_id,
                "url": candidate.get("source_url"),
                "title": title,
                "publisher": candidate.get("publisher", candidate.get("source_type", "")),
                "source_class": "primary" if candidate.get("source_type") in ("nasa", "seed") else "secondary",
                "reliability_notes": "Discovered via public automated collector",
            })

        stats["discovered"] += 1
        stats["by_pillar"][category] = stats["by_pillar"].get(category, 0) + 1

    logger.info("Discovery complete: %d new, %d skipped duplicates", stats["discovered"], stats["duplicates_skipped"])
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect candidate topics for CurioDaily")
    parser.add_argument("--include-seeds", action="store_true", default=True, help="Include seed fallback topics")
    parser.add_argument("--db", type=str, default=None, help="Path to database")
    args = parser.parse_args()

    db = Database(args.db)
    stats = collect_all_sources(db, include_seeds=args.include_seeds)
    print(f"Discovery Summary: Discovered {stats['discovered']} topics, Skipped {stats['duplicates_skipped']} duplicates.")
    for pillar, count in stats.get("by_pillar", {}).items():
        print(f"  - {pillar}: {count}")


if __name__ == "__main__":
    main()
