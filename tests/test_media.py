"""
Tests for media asset generation (visuals, TTS audio, subtitles).
"""

from pathlib import Path
from PIL import Image
from media.create_visuals import (
    create_reel_scene_image,
    create_feed_post_image,
    create_carousel_slide_image
)
from media.tts import generate_synthesized_wav
from media.create_captions import create_srt_subtitles


def test_reel_scene_image_dimensions(tmp_path: Path):
    scene = {
        "scene_number": 1,
        "on_screen_text": "THE RULE OF 72",
        "narration": "Most people misunderstand how compounding works.",
    }
    out_file = tmp_path / "scene1.jpg"
    create_reel_scene_image(scene, "The Rule of 72", "money_secrets", out_file)

    assert out_file.exists()
    with Image.open(out_file) as img:
        assert img.size == (1080, 1920)


def test_feed_post_image_dimensions(tmp_path: Path):
    post = {
        "headline": "The Framing Effect",
        "category": "human_psychology",
        "core_insight": "How options are presented changes our decisions.",
        "supporting_fact": "Documented across hundreds of behavioural studies.",
    }
    out_file = tmp_path / "feed.jpg"
    create_feed_post_image(post, out_file)

    assert out_file.exists()
    with Image.open(out_file) as img:
        assert img.size == (1080, 1350)


def test_carousel_slide_image_dimensions(tmp_path: Path):
    slide = {
        "type": "cover",
        "subtitle": "Swipe to learn the formula →",
    }
    out_file = tmp_path / "slide1.jpg"
    create_carousel_slide_image(slide, "The Rule of 72", "money_secrets", 1, 6, out_file)

    assert out_file.exists()
    with Image.open(out_file) as img:
        assert img.size == (1080, 1350)


def test_tts_synthesized_wav_generates_valid_file(tmp_path: Path):
    out_wav = tmp_path / "narration.wav"
    duration = generate_synthesized_wav("This is a test of the speech generator.", out_wav)

    assert out_wav.exists()
    assert out_wav.stat().st_size > 1000
    assert duration > 1.0


def test_srt_subtitles_created(tmp_path: Path):
    scenes = [
        {"scene_number": 1, "start_sec": 0.0, "end_sec": 4.0, "narration": "First scene caption here"},
        {"scene_number": 2, "start_sec": 4.0, "end_sec": 8.0, "narration": "Second scene caption here"},
    ]
    srt_file = tmp_path / "test.srt"
    create_srt_subtitles(scenes, srt_file)

    assert srt_file.exists()
    content = srt_file.read_text(encoding="utf-8")
    assert "00:00:00,000 -->" in content
    assert "First scene" in content


def test_ass_subtitles_created_with_modern_styles(tmp_path: Path):
    from media.create_captions import create_ass_subtitles
    scenes = [
        {"scene_number": 1, "start_sec": 0.0, "end_sec": 4.0, "narration": "First scene with Rule of 72 doubles wealth"},
    ]
    ass_file = tmp_path / "test.ass"
    create_ass_subtitles(scenes, ass_file, category="money_secrets")

    assert ass_file.exists()
    content = ass_file.read_text(encoding="utf-8")
    assert "ModernPill" in content
    assert "Arial Black" in content


def test_normalize_narration_text_expands_symbols():
    from media.tts import normalize_narration_text
    raw = "Investing $10B into AI yields a 2x return and 15% growth."
    normalized = normalize_narration_text(raw)
    assert "10 billion dollars" in normalized
    assert "A.I." in normalized
    assert "2 times" in normalized
    assert "15 percent" in normalized


def test_storyboard_generator_includes_outro_cta():
    from ai.storyboard_generator import generate_reel_storyboard
    script = {
        "title": "Rule of 72",
        "category": "money_secrets",
        "hook": "Imagine two people saving money.",
        "context": "Most of us think in straight lines.",
        "development": "Take the number 72 and divide by return rate.",
        "payoff": "Wealth curves exponentially.",
        "close": "Are you letting time work for you?"
    }
    storyboard = generate_reel_storyboard(script)
    assert len(storyboard) == 7
    last_scene = storyboard[-1]
    assert last_scene["section"] == "outro"
    assert "follow for daily tips on CurioDaily" in last_scene["narration"]
    assert last_scene["on_screen_text"] == "FOLLOW @CURIODAILY"


def test_outro_scene_image_rendering(tmp_path: Path):
    from media.create_visuals import create_reel_scene_image
    outro_scene = {
        "scene_number": 7,
        "section": "outro",
        "visual_type": "outro",
        "narration": "If you like this, follow for daily tips on CurioDaily so you don't miss out.",
        "on_screen_text": "FOLLOW @CURIODAILY",
        "visual_description": "CurioDaily branded outro card with follow call-to-action."
    }
    img_path = tmp_path / "outro.jpg"
    create_reel_scene_image(outro_scene, "Rule of 72", "money_secrets", img_path)
    assert img_path.exists()
    assert img_path.stat().st_size > 10000
    with Image.open(img_path) as im:
        assert im.size == (1080, 1920)
