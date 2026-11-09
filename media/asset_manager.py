"""
Asset Manager for tracking, caching, and cataloging visual and audio assets.
Maintains provenance, license, and attribution metadata.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


class AssetManager:
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.output_dir / "asset_manifest.json"

    def get_content_dir(self, content_id: str) -> Path:
        content_dir = self.output_dir / content_id
        content_dir.mkdir(parents=True, exist_ok=True)
        return content_dir

    def record_asset(
        self,
        content_id: str,
        file_path: Path | str,
        asset_type: str,
        source_url: str = "",
        license_name: str = "Original CurioDaily / Public Domain",
        attribution_text: str = "",
    ) -> Dict[str, Any]:
        """
        Record metadata for a generated or downloaded media asset.
        """
        path_obj = Path(file_path)
        asset_id = hashlib.md5(f"{content_id}_{path_obj.name}".encode()).hexdigest()[:10]
        size_bytes = path_obj.stat().st_size if path_obj.exists() else 0

        asset_record = {
            "asset_id": asset_id,
            "content_id": content_id,
            "filename": path_obj.name,
            "file_path": str(path_obj.resolve()),
            "asset_type": asset_type,
            "size_bytes": size_bytes,
            "source_url": source_url,
            "license": license_name,
            "attribution": attribution_text,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self._append_to_manifest(content_id, asset_record)
        return asset_record

    def _append_to_manifest(self, content_id: str, record: Dict[str, Any]) -> None:
        manifest: Dict[str, Any] = {}
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception:
                manifest = {}

        if content_id not in manifest:
            manifest[content_id] = []
        manifest[content_id].append(record)

        try:
            with open(self.manifest_file, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        except Exception as exc:
            logger.warning("Failed saving asset manifest: %s", exc)
