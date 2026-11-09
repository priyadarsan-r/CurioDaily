"""
Gemini / Imagen 3 Image & GIF Provider.
Generates ultra-high-resolution 9:16 vertical images using Google's Imagen 3 API,
and converts animated scene clips into high-quality vertical GIFs.
"""

from __future__ import annotations

import base64
import logging
import os
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image
import requests

from ai.gemini_director import get_gemini_api_key
from media.ffmpeg_utils import get_ffmpeg_binary
from media.providers.base import ImageProvider

logger = logging.getLogger(__name__)
USER_AGENT = "CurioDailyGeminiEngine/1.0 (contact@curiodaily.org)"


def download_base64_image(b64_data: str, dest_path: Path) -> bool:
    """Decode base64 image data and save to file with Pillow verification."""
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        img_bytes = base64.b64decode(b64_data)
        with open(dest_path, "wb") as f:
            f.write(img_bytes)

        with Image.open(dest_path) as im:
            im.verify()
        return True
    except Exception as exc:
        logger.debug("Failed saving base64 image to %s: %s", dest_path, exc)
        dest_path.unlink(missing_ok=True)
        return False


class GeminiImagenProvider(ImageProvider):
    """
    Google Imagen 3 API provider for 9:16 vertical photorealistic image generation.
    Utilizes user's Gemini AI Pro / Google AI API key.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_gemini_api_key()

    @property
    def name(self) -> str:
        return "gemini_imagen3"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def fetch_image(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str = "9:16",
        keywords: Optional[str] = None
    ) -> bool:
        """
        Generate image using Google Imagen 3 (imagen-3.0-generate-002).
        Falls back to Pollinations AI if key is unconfigured or rate limited.
        """
        if self.is_available():
            if self._call_imagen_api(prompt, output_path, aspect_ratio=aspect_ratio):
                logger.info("Generated premium image via Google Imagen 3 for: %s", prompt[:60])
                return True

        # Fallback to high-detail Pollinations AI
        logger.debug("Gemini key unavailable or call failed. Using high-detail Pollinations fallback.")
        return self._fallback_pollinations(prompt, output_path)

    def _call_imagen_api(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str = "9:16"
    ) -> bool:
        """Call Google Imagen 3 endpoint via REST API."""
        models = ["imagen-3.0-generate-002", "imagen-3.0-generate-001"]
        headers = {
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT
        }
        
        # Optimize prompt for vertical ratio
        clean_prompt = prompt.strip()
        if "vertical" not in clean_prompt.lower():
            clean_prompt = f"vertical 9:16 portrait documentary photograph, 8k resolution, {clean_prompt}"

        payload = {
            "instances": [
                {"prompt": clean_prompt}
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": aspect_ratio,
                "personGeneration": "ALLOW_ADULT",
                "outputMimeType": "image/jpeg"
            }
        }

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={self.api_key}"
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30.0)
                if resp.status_code == 200:
                    data = resp.json()
                    preds = data.get("predictions", [])
                    if preds:
                        b64_str = preds[0].get("bytesBase64Encoded")
                        if b64_str and download_base64_image(b64_str, output_path):
                            return True
                else:
                    logger.debug("Imagen model %s returned status %d: %s", model, resp.status_code, resp.text[:200])
            except Exception as exc:
                logger.debug("Imagen API call error on %s: %s", model, exc)

        return False

    def _fallback_pollinations(self, prompt: str, output_path: Path) -> bool:
        """Fallback to free Pollinations AI diffusion."""
        import random
        seed = random.randint(10000, 999999)
        clean_p = urllib.parse.quote(prompt[:140])
        url = f"https://image.pollinations.ai/prompt/{clean_p}?width=720&height=1280&nologo=true&seed={seed}"
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=25.0)
            if resp.status_code == 200 and len(resp.content) > 8000:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                with Image.open(output_path) as im:
                    im.verify()
                return True
        except Exception as exc:
            logger.debug("Pollinations fallback error: %s", exc)
        return False


def convert_video_clip_to_gif(
    clip_path: Path,
    gif_path: Path,
    fps: int = 15,
    width: int = 540
) -> bool:
    """
    Convert an MP4 video clip into a smooth, color-optimized vertical GIF
    using FFmpeg two-pass palettegen.
    """
    ffmpeg = get_ffmpeg_binary()
    if not ffmpeg or not clip_path.exists():
        return False

    gif_path.parent.mkdir(parents=True, exist_ok=True)
    # 2-pass palette generation for GIF quality
    vf = f"fps={fps},scale={width}:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5"

    cmd = [
        ffmpeg, "-y",
        "-i", str(clip_path),
        "-vf", vf,
        str(gif_path)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30.0)
        return res.returncode == 0 and gif_path.exists() and gif_path.stat().st_size > 5000
    except Exception as exc:
        logger.debug("GIF conversion failed for %s: %s", clip_path, exc)
        return False
