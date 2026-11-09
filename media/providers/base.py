"""
Base interfaces and data structures for AI Video and Image generation providers.
"""

from __future__ import annotations

import abc
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def compute_prompt_hash(prompt: str, extra: str = "") -> str:
    """Generate a deterministic 12-char hash for caching assets."""
    combined = f"{prompt.strip().lower()}:{extra}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:12]


class VideoProvider(abc.ABC):
    """Abstract interface for all video generation and stock video providers."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Provider identifier name."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if provider credentials or dependencies are configured."""
        pass

    @abc.abstractmethod
    def generate_clip(
        self,
        prompt: str,
        duration: float,
        output_path: Path,
        aspect_ratio: str = "9:16",
        camera_movement: str = "slow_zoom_in",
        keywords: Optional[str] = None
    ) -> bool:
        """
        Generate or fetch a short moving video clip.
        Returns True if output_path is written successfully.
        """
        pass


class ImageProvider(abc.ABC):
    """Abstract interface for all AI and internet image providers."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Provider identifier name."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured."""
        pass

    @abc.abstractmethod
    def fetch_image(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str = "9:16",
        keywords: Optional[str] = None
    ) -> bool:
        """
        Generate or download a high-resolution still image.
        Returns True if output_path is written successfully.
        """
        pass
