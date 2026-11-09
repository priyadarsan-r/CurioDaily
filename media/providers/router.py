"""
Media Provider Router with Multi-Tier Fallback, Caching, and Visual Diversity Enforcement.
Orchestrates AI video generation, stock footage, AI images, archival photography,
and the local Ken Burns camera motion engine while guaranteeing at least 10 different visuals.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from media.media_fetcher import (
    ReelMediaRegistry,
    resolve_distinct_scene_clip,
    ensure_minimum_ten_unique_visuals,
)
from media.providers.video_providers import KenBurnsVideoProvider

logger = logging.getLogger(__name__)


class MediaRouter:
    """
    Intelligently routes scene visual requests across AI video, stock video,
    AI image generation, public domain archives, and the Ken Burns animator.
    Enforces strict visual diversity across all scenes within a Reel.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path(__file__).resolve().parent.parent.parent / "output" / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ken_burns = KenBurnsVideoProvider()
        self.registry = ReelMediaRegistry("cinematic_reel")

    def reset_session(self, content_id: str = "cinematic_reel") -> None:
        """Start a new Reel media session with a clean deduplication registry."""
        self.registry = ReelMediaRegistry(content_id)

    def resolve_scene_clip(
        self,
        scene: Dict[str, Any],
        topic_title: str,
        category: str,
        scene_dur: float,
        content_dir: Path,
        idx: int
    ) -> Path:
        """
        Generate or fetch an MP4 video clip for the scene with exact duration.
        Guarantees a valid 1080x1920 MP4 file with unique visual content.
        """
        return resolve_distinct_scene_clip(
            scene=scene,
            topic_title=topic_title,
            category=category,
            scene_dur=scene_dur,
            content_dir=content_dir,
            scene_idx=idx,
            registry=self.registry
        )

    def ensure_minimum_diversity(
        self,
        scenes: List[Dict[str, Any]],
        topic_title: str,
        category: str,
        content_dir: Path,
        target: int = 10
    ) -> int:
        """Guarantee that at least target (e.g. 10) unique visual assets are used in the Reel."""
        return ensure_minimum_ten_unique_visuals(
            scenes=scenes,
            topic_title=topic_title,
            category=category,
            content_dir=content_dir,
            registry=self.registry,
            min_unique_target=target
        )
