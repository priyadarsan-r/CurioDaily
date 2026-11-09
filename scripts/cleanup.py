"""
Cleanup script for managing temporary media output and disk space.
Retains database and report files while cleaning up old media outputs.
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def cleanup_temporary_assets(max_age_hours: int = 72, dry_run: bool = False) -> int:
    """Delete intermediate generated assets older than max_age_hours."""
    if not OUTPUT_DIR.exists():
        return 0

    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    deleted_count = 0

    for item in OUTPUT_DIR.iterdir():
        if item.name == "asset_manifest.json":
            continue

        try:
            mtime = item.stat().st_mtime
            if mtime < cutoff:
                if dry_run:
                    print(f"Would delete: {item}")
                else:
                    if item.is_dir():
                        import shutil
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    print(f"Deleted: {item}")
                deleted_count += 1
        except Exception as exc:
            logger.warning("Could not delete %s: %s", item, exc)

    return deleted_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Cleanup old temporary assets")
    parser.add_argument("--hours", type=int, default=72, help="Retention period in hours")
    parser.add_argument("--dry-run", action="store_true", help="Print items without deleting")
    args = parser.parse_args()

    count = cleanup_temporary_assets(max_age_hours=args.hours, dry_run=args.dry_run)
    print(f"Cleanup finished. Total items {'scanned' if args.dry_run else 'deleted'}: {count}")


if __name__ == "__main__":
    main()
