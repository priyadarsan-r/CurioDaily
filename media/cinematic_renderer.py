"""
Cinematic Video Rendering Engine.
Assembles 15-20 scene video clips, mixed multi-track audio (voice + BGM + SFX),
applies documentary color grading, and burns modern kinetic ASS captions.
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from media.ffmpeg_utils import get_ffmpeg_binary

logger = logging.getLogger(__name__)


class CinematicRenderer:
    """
    Renders high-retention 1080x1920 vertical videos using FFmpeg
    with cinematic color grading, audio ducking, and kinetic captions.
    """

    def __init__(self):
        self.ffmpeg = get_ffmpeg_binary()

    def render_cinematic_video(
        self,
        scene_clip_paths: List[Path],
        scene_durations: List[float],
        master_audio_path: Path,
        subtitles_ass_path: Path,
        output_mp4_path: Path,
        fps: int = 30
    ) -> bool:
        """
        Assemble scene clips and master audio into a vertical 1080x1920 30FPS MP4.
        """
        if not self.ffmpeg:
            logger.error("FFmpeg executable missing.")
            return False

        output_mp4_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Generate FFmpeg concat list with forward-slash safe relative paths
        concat_file = output_mp4_path.parent / "concat_scenes.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for p in scene_clip_paths:
                safe_path = str(p.resolve()).replace("\\", "/")
                f.write(f"file '{safe_path}'\n")

        # 2. Configure Subtitle Filter
        sub_filter = ""
        if subtitles_ass_path.exists():
            try:
                rel_sub = os.path.relpath(subtitles_ass_path).replace("\\", "/")
            except Exception:
                rel_sub = str(subtitles_ass_path.resolve()).replace("\\", "/")
            sub_filter = f"subtitles='{rel_sub}'"

        # 3. Cinematic Color Grading Filter Chain
        # - Scale & crop insurance to strictly guarantee 1080x1920
        # - Subtle documentary color grading (high-contrast clarity, saturation +10%)
        # - Subtitle overlay
        filters = [
            "scale=1080:1920:force_original_aspect_ratio=increase",
            "crop=1080:1920",
            "eq=contrast=1.05:saturation=1.08:brightness=-0.01",
        ]
        if sub_filter:
            filters.append(sub_filter)

        vf_chain = ",".join(filters)

        cmd = [
            self.ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file.resolve()),
            "-i", str(master_audio_path.resolve()),
            "-vf", vf_chain,
            "-r", str(fps),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_mp4_path.resolve())
        ]

        logger.info(f"Executing cinematic FFmpeg render: {len(scene_clip_paths)} scenes -> {output_mp4_path.name}")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
            if res.returncode == 0 and output_mp4_path.exists() and output_mp4_path.stat().st_size > 100000:
                logger.info(f"Cinematic video exported successfully: {output_mp4_path.stat().st_size:,} bytes")
                return True
            logger.warning(f"FFmpeg render failed: {res.stderr}")
        except Exception as exc:
            logger.error(f"Render exception: {exc}")

        return False
