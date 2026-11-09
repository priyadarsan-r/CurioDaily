"""
Unit tests for Gemini image provider diversity, deduplication, and 100% unique visual enforcement.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from PIL import Image
import pytest

from media.media_fetcher import ReelMediaRegistry
from media.providers.gemini_image_provider import GeminiImagenProvider
from media.providers.image_providers import (
    WikimediaImageProvider,
    extract_clean_search_query,
    crop_and_resize_to_vertical,
)


def test_extract_clean_search_query_strips_camera_jargon():
    """Verify camera jargon and prompts like 'Award-winning 35mm...' are stripped."""
    prompt1 = (
        "Award-winning 35mm cinematic photograph, vertical 9:16, medium shot of two "
        "diverse business partners intensely debating over a tabletop with physical cash stacks, "
        "8k resolution, photorealistic, no text, no watermark"
    )
    q1 = extract_clean_search_query(prompt1)
    assert "award-winning" not in q1.lower()
    assert "35mm" not in q1.lower()
    assert "photorealistic" not in q1.lower()
    assert any(w in q1.lower() for w in ["business", "partners", "debating", "cash", "stacks"])

    prompt2 = (
        "Award-winning 35mm cinematic photograph, vertical 9:16, massive antique bank vault door "
        "swinging open revealing heavy gold bullion bars, dramatic chiaroscuro lighting, 8k resolution"
    )
    q2 = extract_clean_search_query(prompt2)
    assert q1 != q2  # Search queries for different scenes must never be identical
    assert any(w in q2.lower() for w in ["bank", "vault", "gold", "bullion"])


def test_crop_and_resize_to_vertical(tmp_path: Path):
    """Verify arbitrary sized images are cropped and resized to 1080x1920."""
    test_img = tmp_path / "landscape.jpg"
    # Create landscape 1920x1080 image
    Image.new("RGB", (1920, 1080), (120, 50, 20)).save(test_img)

    assert crop_and_resize_to_vertical(test_img, width=1080, height=1920) is True

    with Image.open(test_img) as im:
        assert im.size == (1080, 1920)


def test_gemini_imagen_provider_guarantees_10_unique_hashes(tmp_path: Path):
    """
    Test that 10 sequential scene calls to GeminiImagenProvider generate
    10 completely unique images with 10 distinct MD5 hashes (zero duplicates).
    """
    provider = GeminiImagenProvider(api_key="mock_invalid_key_forces_fallback")
    registry = ReelMediaRegistry("test_diversity_reel")

    scene_prompts = [
        "Executive debating strategy in sunlit office with cash stacks on table",
        "Two professionals walking briskly down Manhattan Fifth Avenue in morning sun",
        "Heavy steel bank vault door swinging open revealing rows of gold bullion",
        "Traders reacting intensely at financial trading terminal with multiple screens",
        "Macro close-up of hands signing legal investment contract with fountain pen",
        "High-angle view of modern skyscraper glass boardroom overlooking city",
        "Low-angle tracking shot of sports car driving along coastal highway at dusk",
        "Two partners shaking hands in industrial loft after successful negotiation",
        "Cinematic slow-motion shot of money passing between hands under soft light",
        "Dramatic silhouette of entrepreneur looking out floor-to-ceiling windows"
    ]

    image_paths = []
    hashes = set()

    for idx, prompt in enumerate(scene_prompts, start=1):
        out_path = tmp_path / f"scene_{idx:02d}.jpg"
        success = provider.fetch_image(
            prompt=prompt,
            output_path=out_path,
            aspect_ratio="9:16",
            scene_idx=idx,
            registry=registry,
            category="money_secrets"
        )
        assert success is True
        assert out_path.exists()
        assert out_path.stat().st_size > 5000

        # Verify 1080x1920 vertical dimensions
        with Image.open(out_path) as im:
            assert im.size == (1080, 1920)

        h = hashlib.md5(out_path.read_bytes()).hexdigest()
        assert h not in hashes, f"Scene {idx} produced duplicate hash {h}!"
        hashes.add(h)
        registry.register_asset(idx, out_path, "image")
        image_paths.append(out_path)

    # Strictly 10 unique hashes across 10 scenes
    assert len(hashes) == 10
    assert len(image_paths) == 10
    assert registry.get_unique_count() == 10
