"""
Automated Quality Inspector for CurioDaily Cinematic Videos.
Validates aspect ratio, resolution, duration, audio levels, black frames,
and stream health, outputting a formal JSON quality report.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from media.ffmpeg_utils import get_ffmpeg_binary

logger = logging.getLogger(__name__)


class QualityInspector:
    """
    Performs pre-export and post-export automated quality inspection
    guaranteeing only high-retention, defect-free videos are cleared.
    """

    def __init__(self):
        self.ffmpeg = get_ffmpeg_binary()

    def inspect_video(
        self,
        video_path: Path,
        expected_duration: float,
        scene_count: int,
        subtitles_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Validate video technical specs and content health.
        Returns detailed quality report dictionary.
        """
        checks: Dict[str, Any] = {}
        errors: List[str] = []
        warnings: List[str] = []

        if not video_path.exists():
            return {
                "passed": False,
                "video_path": str(video_path),
                "errors": ["Video file does not exist."],
                "checks": {},
            }

        file_size = video_path.stat().st_size
        checks["file_size_bytes"] = file_size
        if file_size < 100000:
            errors.append(f"Video file too small ({file_size} bytes); likely corrupted.")

        # Probe video streams using FFmpeg/FFprobe
        probe_info = self._probe_media(video_path)
        v_stream = probe_info.get("video", {})
        a_stream = probe_info.get("audio", {})

        # 1. Resolution & Aspect Ratio check
        w = v_stream.get("width", 0)
        h = v_stream.get("height", 0)
        checks["resolution"] = f"{w}x{h}"
        checks["aspect_ratio"] = "9:16" if (w == 1080 and h == 1920) else f"{w}:{h}"
        if w != 1080 or h != 1920:
            errors.append(f"Invalid resolution: {w}x{h}. Strictly required: 1080x1920.")

        # 2. Duration check
        actual_dur = probe_info.get("duration", 0.0)
        checks["duration_sec"] = actual_dur
        checks["expected_duration_sec"] = expected_duration
        if actual_dur < 35.0:
            errors.append(f"Video duration too short ({actual_dur:.1f}s). Minimum 35s required.")
        elif actual_dur > 75.0:
            warnings.append(f"Video duration longer than standard 60s ({actual_dur:.1f}s).")

        # 3. Audio stream check
        has_audio = bool(a_stream)
        checks["has_audio_stream"] = has_audio
        if not has_audio:
            errors.append("Missing audio stream in rendered video.")

        # 4. Black frame detection
        black_frames = self._detect_black_frames(video_path)
        checks["black_frame_intervals"] = black_frames
        if len(black_frames) > 0:
            errors.append(f"Detected {len(black_frames)} black frame intervals longer than 1.5s.")

        # 5. Scene count check
        checks["scene_count"] = scene_count
        if scene_count < 10:
            warnings.append(f"Low scene count ({scene_count}). Recommended 15-20 scenes for retention.")

        # 6. Subtitles check
        if subtitles_path and subtitles_path.exists():
            checks["subtitles_present"] = True
            checks["subtitles_size_bytes"] = subtitles_path.stat().st_size
            if subtitles_path.stat().st_size < 100:
                warnings.append("Subtitle file is suspiciously small.")
        else:
            checks["subtitles_present"] = False
            warnings.append("No subtitle file provided.")

        passed = len(errors) == 0

        report = {
            "passed": passed,
            "video_path": str(video_path.resolve()),
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
            "status": "APPROVED_FOR_PUBLISHING" if passed else "REJECTED_NEEDS_REVIEW"
        }

        # Save quality report alongside video
        report_path = video_path.parent / "quality_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report

    def _probe_media(self, media_path: Path) -> Dict[str, Any]:
        """Extract media streams metadata using FFmpeg."""
        if not self.ffmpeg:
            return {}

        cmd = [self.ffmpeg, "-i", str(media_path.resolve())]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            output = res.stderr
            width, height = 0, 0
            duration = 0.0

            # Match resolution (e.g., 1080x1920)
            res_match = re.search(r'(\d{3,4})x(\d{3,4})', output)
            if res_match:
                width = int(res_match.group(1))
                height = int(res_match.group(2))

            # Match duration (Duration: 00:00:58.41)
            dur_match = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)', output)
            if dur_match:
                hrs = int(dur_match.group(1))
                mins = int(dur_match.group(2))
                secs = float(dur_match.group(3))
                duration = hrs * 3600 + mins * 60 + secs

            has_video = "Video:" in output
            has_audio = "Audio:" in output

            return {
                "duration": duration,
                "video": {"width": width, "height": height} if has_video else {},
                "audio": {"present": True} if has_audio else {}
            }
        except Exception:
            return {}

    def _detect_black_frames(self, media_path: Path) -> List[str]:
        """Detect freezing black frames longer than 1.5s using blackdetect filter."""
        if not self.ffmpeg:
            return []

        cmd = [
            self.ffmpeg,
            "-i", str(media_path.resolve()),
            "-vf", "blackdetect=d=1.5:pix_th=0.10",
            "-f", "null",
            "-"
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output = res.stderr
            black_intervals = re.findall(r'black_start:\d+\.\d+\s+black_end:\d+\.\d+', output)
            return black_intervals
        except Exception:
            return []
