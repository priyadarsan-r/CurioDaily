"""
Master Orchestrator for the CurioDaily AI-Powered Cinematic Video Generator.
Coordinates Scene Breakdown (15-20 scenes), Voice Synthesis, Media Routing,
Sound Design (Music + SFX + Ducking), Rendering, and Automated Quality Inspection.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai.cinematic_director import CinematicDirector
from media.asset_manager import AssetManager
from media.cinematic_renderer import CinematicRenderer
from media.create_captions import create_ass_subtitles, create_srt_subtitles
from media.providers.router import MediaRouter
from media.quality_inspector import QualityInspector
from media.sound_design import SoundDesigner
from media.tts import TTSManager

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


class CinematicVideoGenerator:
    """
    End-to-end generator converting any 1-minute narration script into a
    high-retention cinematic vertical video (1080x1920, 30fps).
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.director = CinematicDirector()
        self.media_router = MediaRouter()
        self.sound_designer = SoundDesigner()
        self.renderer = CinematicRenderer()
        self.inspector = QualityInspector()
        self.tts = TTSManager()
        self.output_dir = output_dir or Path(__file__).resolve().parent.parent / "output"

    def generate_cinematic_reel(
        self,
        script: str,
        title: str,
        category: str = "daily_mystery",
        content_id: str = "cinematic_reel",
        asset_mgr: Optional[AssetManager] = None
    ) -> Dict[str, Any]:
        """
        Execute full 9-step cinematic generation pipeline.
        """
        asset_mgr = asset_mgr or AssetManager(self.output_dir)
        content_dir = asset_mgr.get_content_dir(content_id)
        content_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"=== Starting Cinematic Generation for: [{category.upper()}] '{title}' ===")

        # 1. Break Script into 15-20 High-Retention Cinematic Scenes
        scenes = self.director.break_into_cinematic_scenes(
            script=script,
            topic_title=title,
            category=category,
            total_estimated_sec=55.0
        )
        logger.info(f"Step 1 Complete: Script divided into {len(scenes)} scenes.")

        # 2. Synthesize Audio Per Scene (Documentary Cadence speed=0.9)
        scene_audio_paths: List[Path] = []
        current_time = 0.0

        for idx, scene in enumerate(scenes, start=1):
            scene_text = scene.get("narration", "").strip() or title
            scene_audio_file = content_dir / f"scene_{idx:02d}_audio.wav"
            res = self.tts.synthesize(scene_text, scene_audio_file, pillar=category, speed=0.9)
            scene_dur = max(2.0, res.get("duration_sec", 3.5))

            scene["start_sec"] = round(current_time, 2)
            scene["end_sec"] = round(current_time + scene_dur, 2)
            scene["duration_sec"] = round(scene_dur, 2)
            current_time += scene_dur
            scene_audio_paths.append(scene_audio_file)

        raw_voice_path = content_dir / "narration_raw.wav"
        total_audio_duration = concat_wav_files(scene_audio_paths, raw_voice_path)
        logger.info(f"Step 2 Complete: Voice synthesized ({total_audio_duration:.1f}s across {len(scenes)} cuts).")

        # 3. Resolve Media Clips (Pexels / Pixabay / AI Video / Archival + Ken Burns motion)
        scene_clip_paths: List[Path] = []
        scene_durations: List[float] = []

        for idx, scene in enumerate(scenes, start=1):
            dur = scene["duration_sec"]
            clip_path = self.media_router.resolve_scene_clip(
                scene=scene,
                topic_title=title,
                category=category,
                scene_dur=dur,
                content_dir=content_dir,
                idx=idx
            )
            scene_clip_paths.append(clip_path)
            scene_durations.append(dur)
            asset_mgr.record_asset(content_id, clip_path, "video_clip", attribution_text="CurioDaily Cinematic Scene")

        logger.info(f"Step 3 Complete: {len(scene_clip_paths)} visual clips rendered.")

        # 4. Generate Subtitles (Modern ASS with Glassmorphism Pill & Highlights)
        srt_path = content_dir / "subtitles.srt"
        ass_path = content_dir / "subtitles.ass"
        create_srt_subtitles(scenes, srt_path)
        create_ass_subtitles(scenes, ass_path, category=category)
        asset_mgr.record_asset(content_id, srt_path, "subtitles")
        asset_mgr.record_asset(content_id, ass_path, "subtitles_ass")
        logger.info("Step 4 Complete: Modern ASS kinetic subtitles formatted.")

        # 5. Sound Design: Mood Music + SFX + Audio Ducking
        master_audio_path = content_dir / "master_audio_mixed.wav"
        self.sound_designer.mix_master_audio(
            voiceover_path=raw_voice_path,
            scenes=scenes,
            category=category,
            total_duration=total_audio_duration,
            output_master_path=master_audio_path
        )
        asset_mgr.record_asset(content_id, master_audio_path, "audio", attribution_text="CurioDaily Mixed Audio")
        logger.info("Step 5 Complete: Master sound design mixed with music & SFX.")

        # 6. Final Video Assembly with Cinematic Color Grading
        final_mp4_path = content_dir / "reel.mp4"
        self.renderer.render_cinematic_video(
            scene_clip_paths=scene_clip_paths,
            scene_durations=scene_durations,
            master_audio_path=master_audio_path,
            subtitles_ass_path=ass_path,
            output_mp4_path=final_mp4_path
        )
        asset_mgr.record_asset(content_id, final_mp4_path, "video", attribution_text="CurioDaily Cinematic Reel")
        logger.info(f"Step 6 Complete: Video rendered at {final_mp4_path}")

        # 7. Automated Quality Inspection
        quality_report = self.inspector.inspect_video(
            video_path=final_mp4_path,
            expected_duration=total_audio_duration,
            scene_count=len(scenes),
            subtitles_path=ass_path
        )
        logger.info(f"Step 7 Complete: Quality inspection passed: {quality_report['passed']}")

        return {
            "content_id": content_id,
            "title": title,
            "category": category,
            "video_path": str(final_mp4_path.resolve()),
            "duration_sec": total_audio_duration,
            "scene_count": len(scenes),
            "quality_status": quality_report["status"],
            "quality_passed": quality_report["passed"],
            "quality_report": quality_report,
            "storyboard": scenes,
        }
