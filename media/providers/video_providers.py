"""
Implementations of Video Providers: Pexels, Pixabay, Replicate, Pollinations, and KenBurns Local Animator.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from media.ffmpeg_utils import get_ffmpeg_binary
from media.providers.base import VideoProvider, compute_prompt_hash

logger = logging.getLogger(__name__)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def download_stream(url: str, dest_path: Path, timeout: float = 20.0) -> bool:
    """Download video stream with size validation."""
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout, stream=True)
        if resp.status_code == 200:
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
            return dest_path.exists() and dest_path.stat().st_size > 15000
    except Exception as exc:
        logger.debug(f"Failed stream download from {url}: {exc}")
    return False


class PexelsVideoProvider(VideoProvider):
    """Pexels API stock video provider with portrait 9:16 filtering."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PEXELS_API_KEY", "")

    @property
    def name(self) -> str:
        return "pexels"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def generate_clip(
        self,
        prompt: str,
        duration: float,
        output_path: Path,
        aspect_ratio: str = "9:16",
        camera_movement: str = "slow_zoom_in",
        keywords: Optional[str] = None
    ) -> bool:
        if not self.is_available():
            logger.debug("Pexels API key unconfigured.")
            return False

        search_query = keywords or prompt[:40]
        url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(search_query)}&orientation=portrait&per_page=5"
        headers = {"Authorization": self.api_key, "User-Agent": USER_AGENT}

        try:
            resp = requests.get(url, headers=headers, timeout=8.0)
            if resp.status_code != 200:
                logger.debug(f"Pexels returned status {resp.status_code}")
                return False

            videos = resp.json().get("videos", [])
            for vid in videos:
                files = vid.get("video_files", [])
                # Sort to find portrait HD files
                portrait_files = [f for f in files if f.get("width", 0) < f.get("height", 0) and f.get("link")]
                target = portrait_files[0] if portrait_files else (files[0] if files else None)
                if target and target.get("link"):
                    raw_path = output_path.with_suffix(".raw.mp4")
                    if download_stream(target["link"], raw_path):
                        success = self._transcode_to_vertical(raw_path, duration, output_path)
                        if raw_path.exists():
                            raw_path.unlink()
                        if success:
                            return True
        except Exception as exc:
            logger.debug(f"Pexels provider error: {exc}")

        return False

    def _transcode_to_vertical(self, raw_path: Path, duration: float, output_path: Path) -> bool:
        ffmpeg = get_ffmpeg_binary()
        if not ffmpeg:
            return False
        vf = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fade=t=in:st=0:d=0.3,fade=t=out:st={max(0.5, duration-0.3):.2f}:d=0.3"
        cmd = [
            ffmpeg, "-y", "-i", str(raw_path), "-t", str(duration),
            "-vf", vf, "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(output_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        return res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 10000


class PixabayVideoProvider(VideoProvider):
    """Pixabay API stock video provider."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PIXABAY_API_KEY", "")

    @property
    def name(self) -> str:
        return "pixabay"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def generate_clip(
        self,
        prompt: str,
        duration: float,
        output_path: Path,
        aspect_ratio: str = "9:16",
        camera_movement: str = "slow_zoom_in",
        keywords: Optional[str] = None
    ) -> bool:
        if not self.is_available():
            return False

        query = keywords or prompt[:40]
        url = f"https://pixabay.com/api/videos/?key={self.api_key}&q={urllib.parse.quote(query)}&per_page=5"
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=8.0)
            if resp.status_code != 200:
                return False
            hits = resp.json().get("hits", [])
            for hit in hits:
                vids = hit.get("videos", {})
                chosen = vids.get("medium") or vids.get("large") or vids.get("small")
                if chosen and chosen.get("url"):
                    raw_path = output_path.with_suffix(".raw.mp4")
                    if download_stream(chosen["url"], raw_path):
                        ffmpeg = get_ffmpeg_binary()
                        if ffmpeg:
                            vf = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fade=t=in:st=0:d=0.3,fade=t=out:st={max(0.5, duration-0.3):.2f}:d=0.3"
                            cmd = [ffmpeg, "-y", "-i", str(raw_path), "-t", str(duration), "-vf", vf, "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(output_path)]
                            subprocess.run(cmd, capture_output=True, timeout=90)
                        if raw_path.exists():
                            raw_path.unlink()
                        if output_path.exists() and output_path.stat().st_size > 10000:
                            return True
        except Exception as exc:
            logger.debug(f"Pixabay error: {exc}")
        return False


class ReplicateVideoProvider(VideoProvider):
    """Replicate API provider for models like Stable Video Diffusion, Kling, or Luma."""

    def __init__(self, api_token: Optional[str] = None, model: str = "stability-ai/stable-video-diffusion"):
        self.api_token = api_token or os.getenv("REPLICATE_API_TOKEN", "")
        self.model = model

    @property
    def name(self) -> str:
        return "replicate"

    def is_available(self) -> bool:
        return bool(self.api_token and len(self.api_token) > 15)

    def generate_clip(
        self,
        prompt: str,
        duration: float,
        output_path: Path,
        aspect_ratio: str = "9:16",
        camera_movement: str = "slow_zoom_in",
        keywords: Optional[str] = None
    ) -> bool:
        if not self.is_available():
            logger.debug("Replicate API token unconfigured.")
            return False

        # If token exists, call Replicate predictions API
        headers = {"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}
        payload = {"version": self.model, "input": {"prompt": prompt, "duration": int(duration)}}
        try:
            resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload, timeout=15.0)
            if resp.status_code in (200, 201):
                pred = resp.json()
                get_url = pred.get("urls", {}).get("get")
                import time
                for _ in range(30):
                    time.sleep(3)
                    poll_resp = requests.get(get_url, headers=headers, timeout=10.0)
                    if poll_resp.status_code == 200:
                        status = poll_resp.json().get("status")
                        if status == "succeeded":
                            output_url = poll_resp.json().get("output")
                            if output_url and download_stream(output_url, output_path):
                                return True
                        elif status in ("failed", "canceled"):
                            break
        except Exception as exc:
            logger.warning(f"Replicate API error: {exc}")

        return False


class KenBurnsVideoProvider(VideoProvider):
    """
    Universal Zero-Budget Local Video Animator.
    Converts a high-resolution image into a vertical 1080x1920 MP4 scene
    with cinematic camera motion (zooms, pans, tilts) and fade transitions.
    """

    def __init__(self):
        self.ffmpeg = get_ffmpeg_binary()

    @property
    def name(self) -> str:
        return "ken_burns_local"

    def is_available(self) -> bool:
        return self.ffmpeg is not None

    def generate_clip(
        self,
        prompt: str,
        duration: float,
        output_path: Path,
        aspect_ratio: str = "9:16",
        camera_movement: str = "slow_zoom_in",
        keywords: Optional[str] = None
    ) -> bool:
        """Called with an image path as prompt or handled by router with image provider."""
        return False

    def animate_image_to_clip(
        self,
        image_path: Path,
        duration: float,
        output_path: Path,
        camera_movement: str = "slow_zoom_in",
        fps: int = 30
    ) -> bool:
        """Animate image into cinematic 1080x1920 MP4 using FFmpeg zoompan and color grading."""
        if not self.ffmpeg or not image_path.exists():
            return False

        output_path.parent.mkdir(parents=True, exist_ok=True)
        total_frames = max(30, int(duration * fps))
        fade_d = 0.35
        fade_out_st = max(0.5, duration - fade_d)

        # Dynamic zoompan expressions based on camera movement
        if camera_movement == "rapid_push_in":
            zoom_expr = f"min(zoom+0.0035,1.25)"
            pan_x = "iw/2-(iw/zoom/2)"
            pan_y = "ih/2-(ih/zoom/2)"
        elif camera_movement == "slow_pan_right":
            zoom_expr = "1.10"
            pan_x = f"min(x+1.5,iw-iw/zoom)"
            pan_y = "ih/2-(ih/zoom/2)"
        elif camera_movement == "tilt_up":
            zoom_expr = "1.10"
            pan_x = "iw/2-(iw/zoom/2)"
            pan_y = f"max(y-1.5,0)"
        else: # slow_zoom_in
            zoom_expr = f"min(zoom+0.0015,1.15)"
            pan_x = "iw/2-(iw/zoom/2)"
            pan_y = "ih/2-(ih/zoom/2)"

        # Cinematic color grading curves (subtle high-contrast documentary look + vignette)
        vf = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"zoompan=z='{zoom_expr}':d={total_frames}:x='{pan_x}':y='{pan_y}':s=1080x1920:fps={fps},"
            f"eq=contrast=1.06:saturation=1.10:brightness=-0.01,"
            f"fade=t=in:st=0:d={fade_d},"
            f"fade=t=out:st={fade_out_st:.2f}:d={fade_d}"
        )

        cmd = [
            self.ffmpeg, "-y",
            "-loop", "1",
            "-i", str(image_path.resolve()),
            "-t", str(duration),
            "-vf", vf,
            "-r", str(fps),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-an",
            str(output_path.resolve())
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 10000
        except Exception as exc:
            logger.warning(f"Ken Burns rendering error: {exc}")
            return False
