"""
Public asset hosting and URL resolver for Instagram media retrieval.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_PUBLIC_BASE_URL = os.getenv("PUBLIC_MEDIA_BASE_URL", "https://raw.githubusercontent.com/curiodaily/curiodaily-engine/gh-pages/media")


def get_public_media_url(file_path: Path | str, base_url: Optional[str] = None) -> str:
    """
    Construct public accessible URL for an asset.
    Assumes media assets in output directory are published to GitHub Pages or static host.
    """
    path_obj = Path(file_path)
    base = (base_url or DEFAULT_PUBLIC_BASE_URL).rstrip("/")
    # Format: base_url / parent_folder / filename
    parent_dir = path_obj.parent.name
    return f"{base}/{parent_dir}/{path_obj.name}"


def stage_asset_for_hosting(file_path: Path | str, staging_dir: Path | str) -> Path:
    """
    Copy media asset to the GitHub Pages staging directory.
    """
    src = Path(file_path)
    dest_dir = Path(staging_dir) / src.parent.name
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    return dest
