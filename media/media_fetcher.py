"""
Media Fetcher & Diversity Engine for CurioDaily Reels.
Fetches at least 10 different real internet images, AI-generated images,
and short video clips with strict deduplication across scenes.
"""

from __future__ import annotations

import hashlib
import logging
import os
import random
import re
import shutil
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from PIL import Image, ImageDraw
import requests

from media.ffmpeg_utils import get_ffmpeg_binary
from media.providers.video_providers import KenBurnsVideoProvider

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
COMMONS_HEADERS = {"User-Agent": "CurioDailyEngine/2.0 (Automated Educational Video; contact@curiodaily.org)"}


class ReelMediaRegistry:
    """
    Session-level media registry for a single Reel.
    Guarantees that no image, video, or diagram is repeated within the same Reel,
    and tracks progress toward the mandatory minimum of at least 10 unique assets.
    """

    def __init__(self, content_id: str = "reel"):
        self.content_id = content_id
        self.used_urls: Set[str] = set()
        self.used_hashes: Set[str] = set()
        self.scene_assets: Dict[int, Dict[str, Any]] = {}

    def is_url_used(self, url: str) -> bool:
        if not url:
            return False
        clean = url.split("?")[0].lower()
        return clean in self.used_urls

    def is_hash_used(self, file_path: Path) -> bool:
        if not file_path.exists():
            return False
        try:
            h = hashlib.md5(file_path.read_bytes()).hexdigest()
            return h in self.used_hashes
        except Exception:
            return False

    def register_asset(
        self,
        scene_idx: int,
        file_path: Path,
        media_type: str,
        url: Optional[str] = None,
        attribution: str = ""
    ) -> str:
        """Register an asset. Returns its MD5 hash."""
        h = ""
        if file_path.exists():
            try:
                h = hashlib.md5(file_path.read_bytes()).hexdigest()
                self.used_hashes.add(h)
            except Exception:
                pass
        if url:
            clean = url.split("?")[0].lower()
            self.used_urls.add(clean)

        self.scene_assets[scene_idx] = {
            "scene_idx": scene_idx,
            "media_type": media_type,
            "file_path": str(file_path),
            "url": url or "",
            "hash": h,
            "attribution": attribution
        }
        return h

    def get_unique_count(self) -> int:
        """Number of unique content hashes registered."""
        return len(self.used_hashes)

    def has_at_least(self, target: int = 10) -> bool:
        return self.get_unique_count() >= target


# Ken Burns animator instance
ken_burns_animator = KenBurnsVideoProvider()


def download_and_validate_image(
    url: str,
    dest_path: Path,
    registry: Optional[ReelMediaRegistry] = None,
    timeout: float = 12.0
) -> bool:
    """Download an image, validate via Pillow, and ensure it is not a duplicate."""
    if registry and registry.is_url_used(url):
        return False

    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, headers=COMMONS_HEADERS, timeout=timeout)
        if resp.status_code != 200 or len(resp.content) < 8000:
            return False

        with open(dest_path, "wb") as f:
            f.write(resp.content)

        # Validate with Pillow
        with Image.open(dest_path) as im:
            im.verify()
            if im.width < 250 or im.height < 250:
                dest_path.unlink(missing_ok=True)
                return False

        # Check hash deduplication
        if registry and registry.is_hash_used(dest_path):
            logger.debug("Duplicate image content hash detected for %s, discarding.", url)
            dest_path.unlink(missing_ok=True)
            return False

        return True
    except Exception as exc:
        logger.debug("Failed downloading image %s: %s", url, exc)
        dest_path.unlink(missing_ok=True)
        return False


def download_and_validate_video(
    url: str,
    dest_path: Path,
    registry: Optional[ReelMediaRegistry] = None,
    timeout: float = 20.0
) -> bool:
    """Download video stream with size and deduplication checks."""
    if registry and registry.is_url_used(url):
        return False

    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout, stream=True)
        if resp.status_code != 200:
            return False

        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)

        if not dest_path.exists() or dest_path.stat().st_size < 15000:
            dest_path.unlink(missing_ok=True)
            return False

        if registry and registry.is_hash_used(dest_path):
            dest_path.unlink(missing_ok=True)
            return False

        return True
    except Exception as exc:
        logger.debug("Failed downloading video %s: %s", url, exc)
        dest_path.unlink(missing_ok=True)
        return False


def transcode_to_vertical_clip(
    raw_path: Path,
    duration: float,
    output_path: Path,
    camera_movement: str = "slow_zoom_in"
) -> bool:
    """Transcode any video file to 1080x1920 30FPS vertical MP4 with audio stripped."""
    ffmpeg = get_ffmpeg_binary()
    if not ffmpeg:
        return False

    fade_out_start = max(0.5, duration - 0.3)
    vf = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,"
        f"fade=t=in:st=0:d=0.25,"
        f"fade=t=out:st={fade_out_start:.2f}:d=0.25"
    )

    cmd = [
        ffmpeg, "-y", "-i", str(raw_path),
        "-t", f"{duration:.2f}",
        "-vf", vf,
        "-r", "30",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-an",
        str(output_path)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=40.0)
        return res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 10000
    except Exception as exc:
        logger.debug("Transcoding error for %s: %s", raw_path, exc)
        return False


def extract_scene_queries(
    scene: Dict[str, Any],
    topic_title: str,
    category: str,
    scene_idx: int
) -> List[str]:
    """
    Generate multiple targeted, high-precision search queries for a scene.
    Prefers clean 1-3 word queries that yield rich image results on Wikimedia/stock.
    """
    queries: List[str] = []
    stopwords = {
        "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "with", "of",
        "by", "from", "how", "why", "what", "is", "are", "this", "that", "scene",
        "card", "graphic", "visual", "showing", "clean", "high", "contrast", "shot",
        "angle", "camera", "lighting", "cinematic", "photorealistic", "ultra", "detailed",
        "curiodaily", "follow", "daily", "tips", "miss", "out", "about", "your", "they",
        "which", "when", "there", "their", "into", "over", "after"
    }

    # 1. From Visual Description
    v_desc = scene.get("visual_description", "")
    if v_desc:
        clean_v = re.sub(r"[^a-zA-Z0-9\s]", " ", v_desc)
        v_words = [w.lower() for w in clean_v.split() if len(w) > 3 and w.lower() not in stopwords]
        if len(v_words) >= 2:
            queries.append(f"{v_words[0]} {v_words[1]}")
        elif v_words:
            queries.append(v_words[0])

    # 2. From Narration
    narration = scene.get("narration", "")
    if narration:
        clean_n = re.sub(r"[^a-zA-Z0-9\s]", " ", narration)
        n_words = [w.lower() for w in clean_n.split() if len(w) > 3 and w.lower() not in stopwords]
        # Pick 2-word pairs across narration
        if len(n_words) >= 2:
            queries.append(f"{n_words[0]} {n_words[1]}")
        if len(n_words) >= 4:
            queries.append(f"{n_words[2]} {n_words[3]}")

    # 3. From Caption Text
    cap = scene.get("caption_text", "")
    if cap and len(cap.split()) <= 3:
        clean_c = re.sub(r"[^a-zA-Z0-9\s]", "", cap).strip()
        if clean_c and clean_c.lower() not in stopwords:
            queries.append(clean_c)

    # 4. Pillar-Aligned Keywords
    cat_words = category.replace("_", " ").split()
    clean_t = re.sub(r"[^a-zA-Z0-9\s]", " ", topic_title)
    t_words = [w.lower() for w in clean_t.split() if len(w) > 3 and w.lower() not in stopwords]

    if t_words:
        kw = t_words[scene_idx % len(t_words)]
        queries.append(f"{cat_words[0]} {kw}")
    else:
        queries.append(cat_words[0])

    # Deduplicate while preserving order
    dedup: List[str] = []
    seen = set()
    for q in queries:
        q_norm = q.strip().lower()
        if q_norm and q_norm not in seen:
            seen.add(q_norm)
            dedup.append(q_norm)

    return dedup[:5]


# =====================================================================
# INDIVIDUAL MEDIA PROVIDERS
# =====================================================================

def search_wikimedia_commons_photos(
    queries: List[str],
    dest_path: Path,
    registry: ReelMediaRegistry,
    limit: int = 8
) -> Optional[Dict[str, str]]:
    """Search Wikimedia Commons File: namespace for unused photos."""
    for query in queries:
        url = (
            f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
            f"&gsrnamespace=6&gsrsearch={urllib.parse.quote(query)}"
            f"&gsrlimit={limit}&prop=imageinfo&iiprop=url|mime|size&format=json"
        )
        try:
            resp = requests.get(url, headers=COMMONS_HEADERS, timeout=6.0)
            if resp.status_code != 200:
                continue
            pages = resp.json().get("query", {}).get("pages", {})
            for _, page in pages.items():
                info = page.get("imageinfo", [{}])[0]
                img_url = info.get("url", "")
                mime = info.get("mime", "")
                size = info.get("size", 0)

                # Filter valid photographic bitmaps
                if not img_url or "image" not in mime or img_url.endswith(".svg"):
                    continue
                if size < 15000:
                    continue
                if registry.is_url_used(img_url):
                    continue

                if download_and_validate_image(img_url, dest_path, registry=registry):
                    return {
                        "source": "Wikimedia Commons",
                        "title": page.get("title", query),
                        "url": img_url,
                        "license": "Creative Commons / Public Domain"
                    }
        except Exception as exc:
            logger.debug("Wikimedia search error for %s: %s", query, exc)
    return None


def search_wikimedia_commons_videos(
    queries: List[str],
    dest_raw_path: Path,
    registry: ReelMediaRegistry,
    limit: int = 5
) -> Optional[Dict[str, str]]:
    """Search Wikimedia Commons for public domain video clips."""
    for query in queries:
        url = (
            f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
            f"&gsrnamespace=6&gsrsearch={urllib.parse.quote(query)}+filetype:video"
            f"&gsrlimit={limit}&prop=imageinfo&iiprop=url|mime|size&format=json"
        )
        try:
            resp = requests.get(url, headers=COMMONS_HEADERS, timeout=8.0)
            if resp.status_code != 200:
                continue
            pages = resp.json().get("query", {}).get("pages", {})
            for _, page in pages.items():
                info = page.get("imageinfo", [{}])[0]
                vid_url = info.get("url", "")
                mime = info.get("mime", "")

                if not vid_url or "video" not in mime:
                    if not any(vid_url.endswith(ext) for ext in [".webm", ".mp4", ".ogv"]):
                        continue
                if registry.is_url_used(vid_url):
                    continue

                if download_and_validate_video(vid_url, dest_raw_path, registry=registry):
                    return {
                        "source": "Wikimedia Commons Video",
                        "title": page.get("title", query),
                        "url": vid_url,
                        "license": "Creative Commons / Public Domain"
                    }
        except Exception as exc:
            logger.debug("Wikimedia video search error for %s: %s", query, exc)
    return None


def search_wikipedia_page_photos(
    queries: List[str],
    dest_path: Path,
    registry: ReelMediaRegistry,
    limit: int = 5
) -> Optional[Dict[str, str]]:
    """Search English Wikipedia articles for lead page thumbnail photos."""
    for query in queries:
        url = (
            f"https://en.wikipedia.org/w/api.php?action=query&format=json&generator=search"
            f"&gsrsearch={urllib.parse.quote(query)}&gsrlimit={limit}&prop=pageimages&pithumbsize=1280"
        )
        try:
            resp = requests.get(url, headers=COMMONS_HEADERS, timeout=6.0)
            if resp.status_code != 200:
                continue
            pages = resp.json().get("query", {}).get("pages", {})
            for _, page in pages.items():
                thumb = page.get("thumbnail", {}).get("source", "")
                if not thumb or thumb.endswith(".svg.png"):
                    continue
                if registry.is_url_used(thumb):
                    continue

                if download_and_validate_image(thumb, dest_path, registry=registry):
                    return {
                        "source": "Wikipedia PageImages",
                        "title": page.get("title", query),
                        "url": thumb,
                        "license": "Creative Commons / Public Domain"
                    }
        except Exception as exc:
            logger.debug("Wikipedia PageImage error for %s: %s", query, exc)
    return None


def search_nasa_archives(
    queries: List[str],
    dest_path: Path,
    registry: ReelMediaRegistry,
    media_type: str = "image"
) -> Optional[Dict[str, str]]:
    """Search NASA Image and Video Library for public domain scientific assets."""
    for query in queries:
        url = f"https://images-api.nasa.gov/search?q={urllib.parse.quote(query)}&media_type={media_type}"
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=8.0)
            if resp.status_code != 200:
                continue
            items = resp.json().get("collection", {}).get("items", [])[:5]
            for it in items:
                title = it.get("data", [{}])[0].get("title", query)
                links = it.get("links", [])
                href = links[0].get("href", "") if links else ""
                if not href or registry.is_url_used(href):
                    continue

                if media_type == "image":
                    if download_and_validate_image(href, dest_path, registry=registry):
                        return {"source": "NASA Archives", "title": title, "url": href, "license": "Public Domain (NASA)"}
                else:
                    if download_and_validate_video(href, dest_path, registry=registry):
                        return {"source": "NASA Archives Video", "title": title, "url": href, "license": "Public Domain (NASA)"}
        except Exception as exc:
            logger.debug("NASA archive search error for %s: %s", query, exc)
    return None


def generate_pollinations_ai_image(
    prompt: str,
    dest_path: Path,
    seed: int,
    registry: ReelMediaRegistry,
    timeout: float = 25.0
) -> bool:
    """Generate vertical 9:16 photorealistic AI image via Pollinations with dedicated seed."""
    clean_p = urllib.parse.quote(prompt[:130])
    url = f"https://image.pollinations.ai/prompt/{clean_p}?width=720&height=1280&nologo=true&seed={seed}"
    return download_and_validate_image(url, dest_path, registry=registry, timeout=timeout)


def search_mixkit_stock_video(
    category: str,
    dest_raw_path: Path,
    registry: ReelMediaRegistry
) -> Optional[Dict[str, str]]:
    """Scrape and transcode free Mixkit stock video clip."""
    category_slugs = {
        "money_secrets": ["money", "business", "technology"],
        "human_psychology": ["people", "technology", "nature"],
        "future_is_here": ["technology", "space", "science"],
        "daily_mystery": ["space", "nature", "science", "technology"],
    }
    slugs = category_slugs.get(category, ["nature", "technology"])
    random.shuffle(slugs)

    for slug in slugs:
        url = f"https://mixkit.co/free-stock-video/{slug}/"
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=7.0)
            if resp.status_code != 200:
                continue
            # Extract 720p or mp4 links
            vids = list(set(re.findall(r'https://assets\.mixkit\.co/videos/\d+/\d+-720\.mp4', resp.text)))
            if not vids:
                vids = list(set(re.findall(r'https://assets\.mixkit\.co/videos/[^\s"\'<>]+\.mp4', resp.text)))

            random.shuffle(vids)
            for v_url in vids:
                if registry.is_url_used(v_url):
                    continue
                if download_and_validate_video(v_url, dest_raw_path, registry=registry):
                    return {
                        "source": "Mixkit Free Video",
                        "title": f"Mixkit {slug} B-roll",
                        "url": v_url,
                        "license": "Mixkit Stock Video Free License"
                    }
        except Exception as exc:
            logger.debug("Mixkit scrape error for %s: %s", slug, exc)
    return None


def search_pexels_video(
    query: str,
    dest_raw_path: Path,
    registry: ReelMediaRegistry
) -> Optional[Dict[str, str]]:
    """Pexels API video search if PEXELS_API_KEY is configured."""
    api_key = os.getenv("PEXELS_API_KEY", "")
    if not api_key or len(api_key) < 10:
        return None

    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=5"
    headers = {"Authorization": api_key, "User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, headers=headers, timeout=8.0)
        if resp.status_code == 200:
            videos = resp.json().get("videos", [])
            for vid in videos:
                files = vid.get("video_files", [])
                portrait = [f for f in files if f.get("width", 0) < f.get("height", 0) and f.get("link")]
                target = portrait[0] if portrait else (files[0] if files else None)
                if target and target.get("link"):
                    v_url = target["link"]
                    if registry.is_url_used(v_url):
                        continue
                    if download_and_validate_video(v_url, dest_raw_path, registry=registry):
                        return {
                            "source": "Pexels Video",
                            "title": f"Pexels Video {vid.get('id')}",
                            "url": v_url,
                            "license": "Pexels Free License"
                        }
    except Exception as exc:
        logger.debug("Pexels video API error: %s", exc)
    return None


# =====================================================================
# MASTER SCENE MEDIA RESOLVER
# =====================================================================

def resolve_distinct_scene_clip(
    scene: Dict[str, Any],
    topic_title: str,
    category: str,
    scene_dur: float,
    content_dir: Path,
    scene_idx: int,
    registry: ReelMediaRegistry
) -> Path:
    """
    Resolve and produce a guaranteed distinct 1080x1920 MP4 video clip for a scene.
    Ensures that at least 10 different images or short videos are fetched across the Reel.
    """
    dest_clip = content_dir / f"scene_{scene_idx:02d}_clip.mp4"
    if dest_clip.exists() and dest_clip.stat().st_size > 15000:
        return dest_clip

    visual_type = scene.get("visual_type", "")
    section = scene.get("section", "")
    narration_text = scene.get("narration", "").lower()
    cam_movement = scene.get("camera_movement", "slow_zoom_in")
    scene_tag = scene.get("caption_text") or scene.get("on_screen_text") or topic_title[:30]

    # 1. Outro Scene: Dedicated branded follow CTA card
    is_outro = (
        visual_type == "outro"
        or section == "outro"
        or "follow for daily tips" in narration_text
        or "so you don't miss out" in narration_text
    )
    if is_outro:
        from media.create_visuals import create_reel_scene_image
        outro_img = content_dir / f"scene_{scene_idx:02d}_outro.jpg"
        create_reel_scene_image(scene, topic_title, category, outro_img)
        ken_burns_animator.animate_image_to_clip(
            image_path=outro_img,
            duration=scene_dur,
            output_path=dest_clip,
            camera_movement="slow_zoom_in"
        )
        registry.register_asset(scene_idx, outro_img, "outro_card", attribution="CurioDaily Outro Card")
        return dest_clip

    # Generate scene-specific query variations
    queries = extract_scene_queries(scene, topic_title, category, scene_idx)
    logger.info("Scene %02d search queries: %s", scene_idx, queries)

    # Alternate media type strategy to guarantee visual dynamics:
    # Odd scenes: try short stock video first -> fallback to real photos -> AI image
    # Even scenes: try real photo / NASA -> AI image -> short video
    prefer_video = (scene_idx % 2 == 1)

    # 2. Try Video Providers if prefer_video
    if prefer_video:
        raw_vid = content_dir / f"raw_video_{scene_idx:02d}.mp4"
        vid_meta = None

        # Pexels Video (if key configured)
        if not vid_meta and queries:
            vid_meta = search_pexels_video(queries[0], raw_vid, registry)

        # Wikimedia Commons Video Search
        if not vid_meta:
            vid_meta = search_wikimedia_commons_videos(queries, raw_vid, registry)

        # Mixkit Free Stock Video Scrape
        if not vid_meta:
            vid_meta = search_mixkit_stock_video(category, raw_vid, registry)

        if vid_meta and raw_vid.exists() and raw_vid.stat().st_size > 15000:
            if transcode_to_vertical_clip(raw_vid, scene_dur, dest_clip, camera_movement=cam_movement):
                registry.register_asset(
                    scene_idx, raw_vid, "stock_video",
                    url=vid_meta.get("url"), attribution=vid_meta.get("title", "Stock Video")
                )
                logger.info("Scene %02d rendered from real video clip: %s", scene_idx, vid_meta.get("title"))
                return dest_clip

    # 3. Try Real Internet Photography (Wikimedia Commons, NASA, Wikipedia)
    chosen_img = content_dir / f"scene_{scene_idx:02d}_raw.jpg"
    photo_meta = None

    # Priority A: Wikimedia Commons File Search (high-resolution real photos)
    photo_meta = search_wikimedia_commons_photos(queries, chosen_img, registry=registry)

    # Priority B: NASA Archives (for astronomy, tech, Earth, mystery)
    if not photo_meta and any(term in category for term in ["mystery", "future", "psychology"]):
        photo_meta = search_nasa_archives(queries, chosen_img, registry=registry)

    # Priority C: Wikipedia PageImages
    if not photo_meta:
        photo_meta = search_wikipedia_page_photos(queries, chosen_img, registry=registry)

    # 4. Try AI Image Generation (Pollinations) with unique seed
    if not photo_meta or not chosen_img.exists():
        ai_prompt = scene.get("ai_prompt") or f"cinematic 8k photograph of {queries[0] if queries else topic_title}, vertical 9:16 portrait documentary"
        seed = random.randint(10000, 999999) + scene_idx * 7919
        if generate_pollinations_ai_image(ai_prompt, chosen_img, seed=seed, registry=registry):
            photo_meta = {
                "source": "Pollinations AI Generation",
                "title": f"AI Visual for Scene {scene_idx}",
                "url": f"pollinations://seed_{seed}",
                "license": "AI Generated"
            }
            logger.info("Scene %02d generated via Pollinations AI (seed=%d)", scene_idx, seed)

    # 5. Last Resort Procedural Fallback
    if not chosen_img.exists() or chosen_img.stat().st_size < 5000:
        from media.create_visuals import create_reel_scene_image
        create_reel_scene_image(scene, topic_title, category, chosen_img)
        photo_meta = {
            "source": "Procedural Diagram Engine",
            "title": f"Concept Frame {scene_idx}",
            "url": f"procedural://scene_{scene_idx}",
            "license": "CurioDaily"
        }

    # Brand overlay & Ken Burns camera animation
    from media.internet_media import overlay_brand_elements_on_image
    branded_img = content_dir / f"scene_{scene_idx:02d}_branded.jpg"
    overlay_brand_elements_on_image(chosen_img, topic_title, category, scene_tag, branded_img)

    ken_burns_animator.animate_image_to_clip(
        image_path=branded_img,
        duration=scene_dur,
        output_path=dest_clip,
        camera_movement=cam_movement
    )

    registry.register_asset(
        scene_idx, chosen_img, "image",
        url=photo_meta.get("url") if photo_meta else "",
        attribution=photo_meta.get("title", f"Scene {scene_idx}") if photo_meta else ""
    )
    logger.info("Scene %02d rendered from %s", scene_idx, photo_meta.get("source") if photo_meta else "Visual Engine")
    return dest_clip


def ensure_minimum_ten_unique_visuals(
    scenes: List[Dict[str, Any]],
    topic_title: str,
    category: str,
    content_dir: Path,
    registry: ReelMediaRegistry,
    min_unique_target: int = 10
) -> int:
    """
    Examine the ReelMediaRegistry. If fewer than 10 unique assets were collected,
    actively generate distinct AI images with unique prompts and seeds until at least
    10 different images/videos exist.
    """
    current_unique = registry.get_unique_count()
    non_outro_scenes = [s for s in scenes if s.get("visual_type") != "outro"]
    target = min(min_unique_target, len(non_outro_scenes))

    if current_unique >= target:
        logger.info("Visual diversity target satisfied: %d unique assets (target: %d)", current_unique, target)
        return current_unique

    logger.warning(
        "Only %d unique visual assets detected (target: %d). Fetching additional distinct visuals...",
        current_unique, target
    )

    # Find scenes that have duplicate hashes or procedural fallbacks
    seen_hashes: Set[str] = set()
    for s in non_outro_scenes:
        s_idx = s.get("scene_number", 1)
        asset_info = registry.scene_assets.get(s_idx)
        h = asset_info.get("hash") if asset_info else ""
        dur = s.get("duration_sec", 3.0)

        if not h or h in seen_hashes:
            # Force replace with a brand new distinct Pollinations AI image
            new_img = content_dir / f"scene_{s_idx:02d}_raw.jpg"
            new_clip = content_dir / f"scene_{s_idx:02d}_clip.mp4"
            seed = random.randint(100000, 9999999) + s_idx * 1337
            prompt = (
                f"cinematic photorealistic vertical portrait 9:16 documentary visual of "
                f"{s.get('visual_description') or topic_title}, high detail dramatic lighting, seed {seed}"
            )
            if generate_pollinations_ai_image(prompt, new_img, seed=seed, registry=registry):
                from media.internet_media import overlay_brand_elements_on_image
                branded_img = content_dir / f"scene_{s_idx:02d}_branded.jpg"
                tag = s.get("caption_text") or topic_title[:30]
                overlay_brand_elements_on_image(new_img, topic_title, category, tag, branded_img)
                ken_burns_animator.animate_image_to_clip(
                    image_path=branded_img,
                    duration=dur,
                    output_path=new_clip,
                    camera_movement=s.get("camera_movement", "slow_zoom_in")
                )
                registry.register_asset(s_idx, new_img, "ai_image", url=f"pollinations://seed_{seed}", attribution=f"AI Visual {s_idx}")
                seen_hashes.add(registry.scene_assets[s_idx]["hash"])
        else:
            seen_hashes.add(h)

        if registry.get_unique_count() >= target:
            break

    final_unique = registry.get_unique_count()
    logger.info("Final unique visual assets count: %d (target: %d)", final_unique, target)
    return final_unique
