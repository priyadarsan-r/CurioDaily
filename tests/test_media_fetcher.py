"""
Tests for media fetching, visual deduplication, and diversity enforcement.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from PIL import Image, ImageDraw
import pytest

from media.media_fetcher import ReelMediaRegistry, extract_scene_queries
from media.diagram_engine import draw_concept_diagram


def test_registry_prevents_duplicate_urls_and_hashes(tmp_path: Path):
    registry = ReelMediaRegistry("test_reel")

    # Create two different sample image files
    f1 = tmp_path / "img1.jpg"
    f2 = tmp_path / "img2.jpg"
    f3_dup = tmp_path / "img3_dup.jpg"

    Image.new("RGB", (100, 100), (255, 0, 0)).save(f1)
    Image.new("RGB", (100, 100), (0, 255, 0)).save(f2)
    Image.new("RGB", (100, 100), (255, 0, 0)).save(f3_dup)  # Identical content to f1

    registry.register_asset(1, f1, "image", url="https://example.com/photo1.jpg")
    registry.register_asset(2, f2, "image", url="https://example.com/photo2.jpg")

    assert registry.is_url_used("https://example.com/photo1.jpg") is True
    assert registry.is_url_used("https://example.com/photo2.jpg") is True
    assert registry.is_url_used("https://example.com/photo3.jpg") is False

    assert registry.is_hash_used(f1) is True
    assert registry.is_hash_used(f2) is True
    assert registry.is_hash_used(f3_dup) is True  # Detected as duplicate content hash

    assert registry.get_unique_count() == 2
    assert registry.has_at_least(2) is True
    assert registry.has_at_least(3) is False


def test_extract_scene_queries_generates_diverse_terms():
    scene1 = {
        "visual_description": "Massive ancient bank vault door swinging open revealing gold bars",
        "narration": "Most people think compound interest is simply slow savings.",
        "caption_text": "THE VAULT OF WEALTH"
    }
    scene2 = {
        "visual_description": "Glowing stock market terminal with green candlestick charts",
        "narration": "When you invest in high yield index funds, the doubling cycle shrinks.",
        "caption_text": "MARKET MULTIPLIER"
    }

    q1 = extract_scene_queries(scene1, "The Rule of 72", "money_secrets", 1)
    q2 = extract_scene_queries(scene2, "The Rule of 72", "money_secrets", 2)

    assert len(q1) > 0
    assert len(q2) > 0
    # Queries for different scenes should be distinct
    assert q1[0] != q2[0]


def test_concept_diagram_diversity_across_scenes(tmp_path: Path):
    """Verify that offline diagram fallback produces distinct images across scenes."""
    hashes = set()
    for s_idx in range(1, 5):
        img = Image.new("RGB", (1080, 1920), (15, 23, 42))
        scene = {"scene_number": s_idx, "narration": f"Scene narration {s_idx}"}
        draw_concept_diagram(img, scene, "money_secrets", (100, 500, 980, 1400), (16, 185, 129), (245, 158, 11))
        out_f = tmp_path / f"diag_{s_idx}.jpg"
        img.save(out_f)
        h = hashlib.md5(out_f.read_bytes()).hexdigest()
        hashes.add(h)

    # Must produce at least 3 distinct diagram types, not 1 repeating graphic
    assert len(hashes) >= 3
