"""
Full Reel creation pipeline.
Combines script, TTS audio synthesis, scene visual frames, captions, and FFmpeg assembly.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from media.asset_manager import AssetManager
from media.create_captions import create_srt_subtitles, create_ass_subtitles
from media.create_visuals import create_reel_scene_image
from media.ffmpeg_utils import assemble_reel_mp4
from media.internet_media import resolve_and_render_scene_clip
from media.quality_inspector import QualityInspector
from media.sound_design import SoundDesigner
from media.tts import TTSManager
from media.visual_fetcher import get_concept_visual

logger = logging.getLogger(__name__)


def concat_wav_files(input_paths: List[Path], output_path: Path) -> float:
    """Concatenate multiple PCM WAV audio files seamlessly into one."""
    import wave
    data = []
    params = None
    for p in input_paths:
        if not Path(p).exists():
            continue
        with wave.open(str(p), "rb") as wf:
            if params is None:
                params = wf.getparams()
            data.append(wf.readframes(wf.getnframes()))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if params and data:
        with wave.open(str(output_path), "wb") as out:
            out.setparams(params)
            for d in data:
                out.writeframes(d)
        with wave.open(str(output_path), "rb") as final_wf:
            return final_wf.getnframes() / float(final_wf.getframerate())
    return 30.0


def build_reel(
    content_record: Dict[str, Any],
    output_dir: Optional[Path] = None,
    asset_mgr: Optional[AssetManager] = None,
    tts_mgr: Optional[TTSManager] = None
) -> Dict[str, Any]:
    content_id = content_record.get("content_id", "test_reel")
    title = content_record.get("title", "")
    category = content_record.get("category", "daily_mystery")
    storyboard = content_record.get("storyboard_json", [])
    narration = content_record.get("script", "") or content_record.get("narration", "")

    asset_mgr = asset_mgr or AssetManager(output_dir)
    tts_mgr = tts_mgr or TTSManager()

    content_dir = asset_mgr.get_content_dir(content_id)

    # 1. Synthesize audio per scene with normal pace (speed=0.9) for exact voice-subtitle-video sync
    scene_audio_paths: List[Path] = []
    current_time = 0.0

    # Ensure storyboard has high visual density (15-20 cuts matching audience retention standards)
    if not storyboard or len(storyboard) < 10:
        from ai.cinematic_director import CinematicDirector
        director = CinematicDirector()
        storyboard = director.break_into_cinematic_scenes(
            script=narration,
            topic_title=title,
            category=category,
            total_estimated_sec=55.0
        )

    # Guarantee that the Reel ends with the official CurioDaily Follow CTA scene
    has_cta = any("follow for daily tips on curiodaily" in s.get("narration", "").lower() for s in storyboard)
    if not has_cta:
        storyboard.append({
            "scene_number": len(storyboard) + 1,
            "section": "outro",
            "narration": "If you like this, follow for daily tips on CurioDaily so you don't miss out.",
            "visual_type": "outro",
            "visual_description": "CurioDaily branded outro card with follow call-to-action.",
            "camera_effect": "ken_burns",
            "on_screen_text": "FOLLOW @CURIODAILY",
            "transition": "fade",
        })

    from media.internet_media import get_reel_registry
    from media.media_fetcher import ensure_minimum_ten_unique_visuals
    reel_reg = get_reel_registry(content_id)

    for idx, scene in enumerate(storyboard, start=1):
        scene_text = scene.get("narration", "").strip() or title
        scene_audio_file = content_dir / f"scene_{idx}_audio.wav"
        # Speed 0.9 provides calm, natural, authoritative narration
        res = tts_mgr.synthesize(scene_text, scene_audio_file, pillar=category, speed=0.9)
        scene_dur = max(2.5, res.get("duration_sec", 4.0))

        scene["start_sec"] = round(current_time, 2)
        scene["end_sec"] = round(current_time + scene_dur, 2)
        scene["duration_sec"] = round(scene_dur, 2)
        current_time += scene_dur
        scene_audio_paths.append(scene_audio_file)

    # Master audio track from exact sequence of scene audios
    audio_path = content_dir / "narration.wav"
    total_audio_duration = concat_wav_files(scene_audio_paths, audio_path)
    asset_mgr.record_asset(content_id, audio_path, "audio", attribution_text="CurioDaily TTS")

    # 2. Render each scene video clip with its EXACT scene duration
    scene_clip_paths: List[Path] = []
    scene_durations: List[float] = []

    for idx, scene in enumerate(storyboard, start=1):
        dur = scene["duration_sec"]
        clip_path = resolve_and_render_scene_clip(
            scene=scene,
            title=title,
            category=category,
            scene_dur=dur,
            content_dir=content_dir,
            idx=idx,
            asset_mgr=asset_mgr,
            content_id=content_id
        )
        scene_clip_paths.append(clip_path)
        scene_durations.append(dur)
        asset_mgr.record_asset(content_id, clip_path, "video_clip", attribution_text="CurioDaily Cinematic Scene Clip")

    # Guarantee at least 10 different images or short videos across scenes
    unique_count = ensure_minimum_ten_unique_visuals(
        scenes=storyboard,
        topic_title=title,
        category=category,
        content_dir=content_dir,
        registry=reel_reg,
        min_unique_target=10
    )
    logger.info("Visual diversity verified: %d unique assets rendered across %d scenes", unique_count, len(storyboard))

    # 3. Generate Subtitles (both .srt and modern styled .ass with keyword highlights & pill box)
    srt_path = content_dir / "subtitles.srt"
    ass_path = content_dir / "subtitles.ass"
    create_srt_subtitles(storyboard, srt_path)
    create_ass_subtitles(storyboard, ass_path, category=category)
    asset_mgr.record_asset(content_id, srt_path, "subtitles")
    asset_mgr.record_asset(content_id, ass_path, "subtitles_ass")

    # 4. Sound Design: Mood Music + SFX + Audio Ducking
    sound_designer = SoundDesigner()
    master_audio_path = content_dir / "master_audio_mixed.wav"
    sound_designer.mix_master_audio(
        voiceover_path=audio_path,
        scenes=storyboard,
        category=category,
        total_duration=total_audio_duration,
        output_master_path=master_audio_path
    )
    final_audio = master_audio_path if master_audio_path.exists() else audio_path
    asset_mgr.record_asset(content_id, final_audio, "audio", attribution_text="CurioDaily Mixed Audio")

    # 5. Assemble Final Reel MP4 with modern ASS subtitles & mixed audio
    mp4_path = content_dir / "reel.mp4"
    assemble_reel_mp4(
        scene_image_paths=scene_clip_paths,
        scene_durations=scene_durations,
        audio_path=final_audio,
        output_path=mp4_path,
        srt_path=ass_path
    )
    asset_mgr.record_asset(content_id, mp4_path, "video", attribution_text="CurioDaily Reel")

    # 6. Automated Quality Inspection
    inspector = QualityInspector()
    quality_report = inspector.inspect_video(
        video_path=mp4_path,
        expected_duration=total_audio_duration,
        scene_count=len(scene_clip_paths),
        subtitles_path=ass_path
    )

    return {
        "content_id": content_id,
        "format": "reel",
        "video_path": str(mp4_path.resolve()),
        "audio_path": str(final_audio.resolve()),
        "subtitles_path": str(srt_path.resolve()),
        "duration_sec": total_audio_duration,
        "scene_count": len(scene_clip_paths),
        "quality_status": quality_report.get("status", "APPROVED"),
        "quality_passed": quality_report.get("passed", True),
        "quality_report": quality_report,
    }
