"""
Internet and AI Media Engine for CurioDaily Reels.
Fetches real stock video clips (Mixkit), real high-res photos (Wikimedia/NASA),
and AI-generated visuals, converting them into 1080x1920 vertical video scenes
with Ken Burns motion and smooth transitions.
"""

from __future__ import annotations

import logging
import re
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont
import requests

from media.ffmpeg_utils import get_ffmpeg_binary

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
WIKI_HEADERS = {"User-Agent": "CurioDailyBot/1.0 (Educational Content Engine; contact@curiodaily.org)"}

# CurioDaily Pillar Category Maps for Mixkit stock video queries
CATEGORY_VIDEO_MAP = {
    "money_secrets": ["money", "business", "technology"],
    "human_psychology": ["people", "technology", "nature"],
    "future_is_here": ["technology", "space", "nature"],
    "daily_mystery": ["space", "nature", "technology"],
}


def download_file(url: str, dest_path: Path, timeout: float = 15.0) -> bool:
    """Download a remote file with user-agent headers and error handling."""
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout, stream=True)
        if resp.status_code == 200:
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
            return dest_path.exists() and dest_path.stat().st_size > 5000
    except Exception as exc:
        logger.debug("Failed downloading %s: %s", url, exc)
    return False


def fetch_mixkit_video_url(category_slug: str) -> Optional[str]:
    """Scrape a free MP4 video URL from Mixkit."""
    url = f"https://mixkit.co/free-stock-video/{category_slug}/"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=8.0)
        if resp.status_code == 200:
            # Prefer 720p resolution
            vids = list(set(re.findall(r'https://assets\.mixkit\.co/videos/\d+/\d+-720\.mp4', resp.text)))
            if not vids:
                vids = list(set(re.findall(r'https://assets\.mixkit\.co/videos/[^\s"\'<>]+\.mp4', resp.text)))
            if vids:
                import random
                return random.choice(vids[:6])
    except Exception as exc:
        logger.debug("Mixkit scrape error for %s: %s", category_slug, exc)
    return None


def fetch_wikimedia_photo_url(query: str) -> Optional[Dict[str, str]]:
    """Search Wikipedia REST / Commons for a high-res real photo."""
    url = (
        f"https://en.wikipedia.org/w/api.php?action=query&format=json&generator=search"
        f"&gsrsearch={urllib.parse.quote(query)}&gsrlimit=3&prop=pageimages&pithumbsize=1280"
    )
    try:
        resp = requests.get(url, headers=WIKI_HEADERS, timeout=6.0)
        if resp.status_code == 200:
            pages = resp.json().get("query", {}).get("pages", {})
            for _, p in pages.items():
                thumb = p.get("thumbnail", {}).get("source")
                if thumb and not thumb.endswith(".svg.png"):
                    return {
                        "url": thumb,
                        "title": p.get("title", query),
                        "source": "Wikimedia Commons",
                        "license": "Creative Commons / Public Domain"
                    }
    except Exception as exc:
        logger.debug("Wikimedia search error for %s: %s", query, exc)
    return None


def fetch_ai_image(prompt: str, dest_path: Path) -> bool:
    """Attempt free AI image generation via Pollinations."""
    clean_prompt = urllib.parse.quote(prompt[:120])
    url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=720&height=1280&nologo=true"
    return download_file(url, dest_path, timeout=20.0)


def overlay_brand_elements_on_image(
    image_path: Path,
    topic_title: str,
    category: str,
    scene_tag: str,
    output_path: Path
) -> Path:
    """
    Apply top brand watermark, category badge, and scene tag
    over a real photo or AI image before video rendering.
    """
    from media.create_visuals import PALETTES, hex_to_rgb, get_font, wrap_text

    palette = PALETTES.get(category, PALETTES["daily_mystery"])
    primary_color = hex_to_rgb(palette["primary"])

    with Image.open(image_path) as img:
        img_rgb = img.convert("RGB")
        target_w, target_h = 1080, 1920

        # Aspect fill cover crop to 1080x1920
        ratio = max(target_w / img_rgb.width, target_h / img_rgb.height)
        new_size = (int(img_rgb.width * ratio), int(img_rgb.height * ratio))
        img_resized = img_rgb.resize(new_size, Image.Resampling.LANCZOS)
        left = (img_resized.width - target_w) // 2
        top = (img_resized.height - target_h) // 2
        cropped = img_resized.crop((left, top, left + target_w, top + target_h))

        draw = ImageDraw.Draw(cropped)

        # Top subtle dark gradient overlay for watermark readability
        for y in range(0, 380):
            alpha = int(180 * (1.0 - y / 380))
            draw.line([(0, y), (target_w, y)], fill=(15, 23, 42))

        # Bottom subtle dark gradient overlay for subtitles readability (near bottom MarginV=55)
        for y in range(1650, target_h):
            draw.line([(0, y), (target_w, y)], fill=(15, 23, 42))

        # Brand Badge & Watermark
        badge_text = palette["badge"]
        badge_font = get_font(30, bold=True)
        draw.rectangle([(70, 160), (70 + len(badge_text) * 20, 210)], fill=primary_color)
        draw.text((82, 168), badge_text, fill=(15, 23, 42), font=badge_font)

        watermark_font = get_font(26, bold=True)
        draw.text((target_w - 230, 172), "@CURIODAILY", fill=(203, 213, 225), font=watermark_font)

        # Title / Scene Tag
        if scene_tag:
            tag_font = get_font(36, bold=True)
            lines = wrap_text(scene_tag, max_chars=30)
            yt = 235
            for line in lines[:2]:
                draw.text((70, yt), line, fill=(255, 255, 255), font=tag_font)
                yt += 48

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(output_path, "JPEG", quality=92)

    return output_path


def render_scene_to_video_clip(
    media_source_path: Path,
    is_video: bool,
    duration: float,
    output_clip_path: Path,
    fps: int = 30
) -> bool:
    """
    Convert an image (with Ken Burns motion) or video clip
    into a vertical 1080x1920 30fps MP4 with smooth fade transitions.
    """
    ffmpeg_bin = get_ffmpeg_binary()
    if not ffmpeg_bin:
        logger.warning("FFmpeg binary missing.")
        return False

    output_clip_path.parent.mkdir(parents=True, exist_ok=True)
    fade_d = 0.4
    fade_out_st = max(0.5, duration - fade_d)

    if is_video:
        # Scale/crop stock video clip to 1080x1920 with fade transitions
        vf = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"fade=t=in:st=0:d={fade_d},"
            f"fade=t=out:st={fade_out_st:.2f}:d={fade_d}"
        )
        cmd = [
            ffmpeg_bin, "-y",
            "-i", str(media_source_path.resolve()),
            "-t", str(duration),
            "-vf", vf,
            "-r", str(fps),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-an",
            str(output_clip_path.resolve())
        ]
    else:
        # Convert image into Ken Burns slow cinematic zoom + fade
        total_frames = int(duration * fps)
        vf = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"zoompan=z='min(zoom+0.0012,1.15)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps},"
            f"fade=t=in:st=0:d={fade_d},"
            f"fade=t=out:st={fade_out_st:.2f}:d={fade_d}"
        )
        cmd = [
            ffmpeg_bin, "-y",
            "-loop", "1",
            "-i", str(media_source_path.resolve()),
            "-t", str(duration),
            "-vf", vf,
            "-r", str(fps),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-an",
            str(output_clip_path.resolve())
        ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return proc.returncode == 0 and output_clip_path.exists()
    except Exception as exc:
        logger.warning("Error rendering scene clip: %s", exc)
        return False


def resolve_and_render_scene_clip(
    scene: Dict[str, Any],
    title: str,
    category: str,
    scene_dur: float,
    content_dir: Path,
    idx: int,
    asset_mgr: Optional[Any] = None,
    content_id: str = "reel"
) -> Path:
    """
    Resolve real video clip or real internet/AI image for the scene,
    and render to a 1080x1920 MP4 scene clip with Ken Burns motion and smooth transitions.
    """
    scene_clip_path = content_dir / f"scene_{idx}_clip.mp4"
    if scene_clip_path.exists() and scene_clip_path.stat().st_size > 10000:
        return scene_clip_path

    from media.create_visuals import create_reel_scene_image

    visual_type = scene.get("visual_type", "")
    section = scene.get("section", "")
    narration_text = scene.get("narration", "").lower()

    # Outro Scene: Directly render the branded CurioDaily CTA card with subtle Ken Burns motion
    if visual_type == "outro" or section == "outro" or "follow for daily tips on curiodaily" in narration_text:
        outro_img = content_dir / f"scene_{idx}_outro.jpg"
        create_reel_scene_image(scene, title, category, outro_img)
        render_scene_to_video_clip(outro_img, is_video=False, duration=scene_dur, output_clip_path=scene_clip_path)
        return scene_clip_path

    scene_tag = scene.get("on_screen_text", title[:30])
    visual_desc = scene.get("visual_description", "")

    # Alternate between video clips and real/AI photos across scenes
    is_video_turn = (idx % 2 == 1)

    # 1. Attempt Video Clip
    if is_video_turn:
        vid_slugs = CATEGORY_VIDEO_MAP.get(category, ["technology", "space"])
        import random
        slug = random.choice(vid_slugs)
        vid_url = fetch_mixkit_video_url(slug)
        if vid_url:
            raw_vid = content_dir / f"raw_video_{idx}.mp4"
            if download_file(vid_url, raw_vid):
                success = render_scene_to_video_clip(raw_vid, is_video=True, duration=scene_dur, output_clip_path=scene_clip_path)
                if success:
                    if asset_mgr:
                        asset_mgr.record_asset(content_id, raw_vid, "video_broll", source_url=vid_url, license_name="Mixkit Free License", attribution_text="Mixkit Stock Video")
                    return scene_clip_path

    # 2. Attempt Real Internet Photo (Wikimedia Commons / Wikipedia)
    photo_info = fetch_wikimedia_photo_url(title)
    if not photo_info:
        photo_info = fetch_wikimedia_photo_url(category.replace("_", " "))

    if photo_info:
        raw_photo = content_dir / f"raw_photo_{idx}.jpg"
        if download_file(photo_info["url"], raw_photo):
            branded_photo = content_dir / f"branded_photo_{idx}.jpg"
            overlay_brand_elements_on_image(raw_photo, title, category, scene_tag, branded_photo)
            success = render_scene_to_video_clip(branded_photo, is_video=False, duration=scene_dur, output_clip_path=scene_clip_path)
            if success:
                if asset_mgr:
                    asset_mgr.record_asset(content_id, raw_photo, "photo", source_url=photo_info["url"], license_name=photo_info["license"], attribution_text=photo_info["title"])
                return scene_clip_path

    # 3. Attempt AI-Generated Image (Pollinations)
    ai_prompt = f"cinematic 8k highly detailed visual of {title}, {visual_desc}, vertical 9:16 portrait"
    raw_ai = content_dir / f"raw_ai_{idx}.jpg"
    if fetch_ai_image(ai_prompt, raw_ai):
        branded_ai = content_dir / f"branded_ai_{idx}.jpg"
        overlay_brand_elements_on_image(raw_ai, title, category, scene_tag, branded_ai)
        success = render_scene_to_video_clip(branded_ai, is_video=False, duration=scene_dur, output_clip_path=scene_clip_path)
        if success:
            if asset_mgr:
                asset_mgr.record_asset(content_id, raw_ai, "ai_image", license_name="AI Generated", attribution_text="CurioDaily AI Generator")
            return scene_clip_path

    # 4. Fallback: Procedural Concept Frame with Ken Burns Motion
    fallback_img = content_dir / f"scene_{idx}.jpg"
    create_reel_scene_image(scene, title, category, fallback_img)
    render_scene_to_video_clip(fallback_img, is_video=False, duration=scene_dur, output_clip_path=scene_clip_path)
    return scene_clip_path
