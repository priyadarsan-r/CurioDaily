"""
Unit tests for the AI-Powered Cinematic Video Generator components:
CinematicDirector, SoundDesigner, MediaRouter, and QualityInspector.
"""

from __future__ import annotations

import json
from pathlib import Path
from PIL import Image
import pytest

from ai.cinematic_director import CinematicDirector
from media.providers.base import compute_prompt_hash
from media.quality_inspector import QualityInspector
from media.sound_design import SoundDesigner, generate_synthetic_ambient_music, generate_synthetic_sfx


def test_cinematic_director_generates_15_to_20_scenes():
    director = CinematicDirector()
    script = (
        "When astronauts first orbited Earth in the 1960s, they peered down at the desolate sands of Mauritania "
        "and saw a giant eye staring back at them. A perfect bullseye, twenty-five miles wide. "
        "Scientists insisted it had to be an asteroid crater. But geologists found zero impact quartz. "
        "The truth was a massive magma dome that swelled and collapsed 100 million years ago. "
        "It is so massive, astronauts on the space station still use it as a visual landmark today."
    )
    scenes = director.break_into_cinematic_scenes(
        script=script,
        topic_title="The Eye of the Sahara",
        category="daily_mystery",
        total_estimated_sec=55.0
    )

    assert 14 <= len(scenes) <= 20
    first = scenes[0]
    assert first["retention_purpose"] == "visual_hook"
    assert first["sound_effect"] in ("cinematic_impact", "whoosh_transition")
    assert "camera_angle" in first
    assert "lighting" in first
    assert "ai_prompt" in first
    assert "caption_text" in first

    last = scenes[-1]
    assert last["visual_type"] == "cinematic_scene"
    assert "outro" not in last["visual_type"]


def test_sound_designer_sfx_and_music_generation(tmp_path: Path):
    sfx_file = tmp_path / "impact.wav"
    generate_synthetic_sfx("cinematic_impact", sfx_file)
    assert sfx_file.exists()
    assert sfx_file.stat().st_size > 10000

    music_file = tmp_path / "ambient.wav"
    generate_synthetic_ambient_music("suspenseful_mystery", 3.0, music_file)
    assert music_file.exists()
    assert music_file.stat().st_size > 50000


def test_prompt_hash_deterministic():
    h1 = compute_prompt_hash("cinematic aerial view of desert eye", "slow_zoom_in:3.5")
    h2 = compute_prompt_hash("cinematic aerial view of desert eye", "slow_zoom_in:3.5")
    h3 = compute_prompt_hash("different prompt", "slow_zoom_in:3.5")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 12


def test_quality_inspector_detects_missing_file(tmp_path: Path):
    inspector = QualityInspector()
    missing_video = tmp_path / "non_existent.mp4"
    report = inspector.inspect_video(missing_video, expected_duration=55.0, scene_count=15)
    assert report["passed"] is False
    assert len(report["errors"]) > 0
