"""
Export daily JSON run summaries and system health metrics.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db import Database

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def generate_daily_report(db: Database) -> Dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Metrics from database
    with db.get_connection() as conn:
        total_topics = conn.execute("SELECT COUNT(*) FROM topics;").fetchone()[0]
        discovered_today = conn.execute("SELECT COUNT(*) FROM topics WHERE discovered_at LIKE ?;", (f"{today}%",)).fetchone()[0]
        total_content = conn.execute("SELECT COUNT(*) FROM content;").fetchone()[0]
        pending_queue = conn.execute("SELECT COUNT(*) FROM publishing_queue WHERE status = 'pending';").fetchone()[0]
        published_items = conn.execute("SELECT COUNT(*) FROM publishing_queue WHERE status = 'published';").fetchone()[0]

    report = {
        "date": today,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topics": {
            "total_lifetime": total_topics,
            "discovered_today": discovered_today,
        },
        "content": {
            "total_pieces_generated": total_content,
            "pending_in_queue": pending_queue,
            "published_total": published_items,
        },
        "system_status": "healthy",
    }

    report_path = REPORTS_DIR / f"daily_report_{today}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Export daily run report")
    parser.add_argument("--db", type=str, default=None, help="Database path")
    args = parser.parse_args()

    db = Database(args.db)
    report = generate_daily_report(db)
    print("=== Daily Engine Report ===")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
