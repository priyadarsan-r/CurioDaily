"""
Media Provider Router with Multi-Tier Fallback, Caching, and Validation.
Orchestrates AI video generation, stock footage, AI images, archival photography,
and the local Ken Burns camera motion engine.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from media.internet_media import overlay_brand_elements_on_image
from media.providers.base import compute_prompt_hash
from media.providers.image_providers import (
    NASAImageProvider,
    PexelsImageProvider,
    PollinationsImageProvider,
    WikimediaImageProvider,
)
from media.providers.video_providers import (
    KenBurnsVideoProvider,
    PexelsVideoProvider,
    PixabayVideoProvider,
    ReplicateVideoProvider,
)

logger = logging.getLogger(__name__)


class MediaRouter:
    """
    Intelligently routes scene visual requests across AI video, stock video,
    AI image generation, public domain archives, and the Ken Burns animator.
    Caches assets to avoid redundant external network requests.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path(__file__).resolve().parent.parent.parent / "output" / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Video Providers in priority order
        self.video_providers = [
            PexelsVideoProvider(),
            PixabayVideoProvider(),
            ReplicateVideoProvider(),
        ]

        # Image Providers in priority order
        self.image_providers = [
            WikimediaImageProvider(),
            NASAImageProvider(),
            PexelsImageProvider(),
            PollinationsImageProvider(),
        ]

        # Local Ken Burns animator
        self.ken_burns = KenBurnsVideoProvider()

    def resolve_scene_clip(
        self,
        scene: Dict[str, Any],
        topic_title: str,
        category: str,
        scene_dur: float,
        content_dir: Path,
        idx: int
    ) -> Path:
        """
        Generate or fetch an MP4 video clip for the scene with exact duration.
        Guarantees a valid 1080x1920 MP4 file is returned.
        """
        dest_clip = content_dir / f"scene_{idx:02d}_clip.mp4"
        if dest_clip.exists() and dest_clip.stat().st_size > 15000:
            return dest_clip

        ai_prompt = scene.get("ai_prompt", "")
        cam_movement = scene.get("camera_movement", "slow_zoom_in")
        visual_type = scene.get("visual_type", "")
        narration = scene.get("narration", "")

        # 1. Outro Scene Handling (Dedicated branded card)
        if visual_type == "outro" or "follow for daily tips" in narration.lower():
            from media.create_visuals import create_reel_scene_image
            outro_img = content_dir / f"scene_{idx:02d}_outro.jpg"
            create_reel_scene_image(scene, topic_title, category, outro_img)
            self.ken_burns.animate_image_to_clip(outro_img, scene_dur, dest_clip, camera_movement="slow_zoom_in")
            if dest_clip.exists():
                return dest_clip

        prompt_hash = compute_prompt_hash(ai_prompt, f"{cam_movement}:{scene_dur:.1f}")
        cached_clip = self.cache_dir / f"clip_{prompt_hash}.mp4"
        if cached_clip.exists() and cached_clip.stat().st_size > 15000:
            logger.info(f"Reusing cached clip for scene {idx} ({prompt_hash})")
            shutil.copy2(cached_clip, dest_clip)
            return dest_clip

        # 2. Try configured Video Providers (alternate to prevent visual monotony)
        if idx % 2 == 1:
            keywords = f"{category.replace('_', ' ')} {topic_title[:25]}"
            for v_prov in self.video_providers:
                if v_prov.is_available():
                    temp_vid = content_dir / f"temp_vid_{idx:02d}.mp4"
                    if v_prov.generate_clip(ai_prompt, scene_dur, temp_vid, keywords=keywords):
                        shutil.copy2(temp_vid, dest_clip)
                        shutil.copy2(temp_vid, cached_clip)
                        try:
                            temp_vid.unlink()
                        except Exception:
                            pass
                        logger.info(f"Generated video clip for scene {idx} using {v_prov.name}")
                        return dest_clip

        # 3. Fallback to Image Providers + Ken Burns Animation
        cached_img = self.cache_dir / f"img_{prompt_hash}.jpg"
        chosen_img = content_dir / f"scene_{idx:02d}_raw.jpg"

        if cached_img.exists() and cached_img.stat().st_size > 5000:
            shutil.copy2(cached_img, chosen_img)
        else:
            image_fetched = False
            # Extract keywords from narration for precise image matching
            words = [w.strip(".,—!?:;\"'") for w in narration.split() if len(w) > 3]
            keywords = " ".join(words[:4]) if words else topic_title

            for i_prov in self.image_providers:
                if i_prov.is_available():
                    if i_prov.fetch_image(ai_prompt, chosen_img, keywords=keywords):
                        shutil.copy2(chosen_img, cached_img)
                        logger.info(f"Fetched visual for scene {idx} using {i_prov.name}")
                        image_fetched = True
                        break

            if not image_fetched:
                # Local procedural fallback diagram/card
                from media.create_visuals import create_reel_scene_image
                create_reel_scene_image(scene, topic_title, category, chosen_img)

        # Apply subtle brand watermark & category badge
        branded_img = content_dir / f"scene_{idx:02d}_branded.jpg"
        scene_tag = scene.get("caption_text", topic_title[:30])
        overlay_brand_elements_on_image(chosen_img, topic_title, category, scene_tag, branded_img)

        # Animate the image with the designated cinematic camera movement
        self.ken_burns.animate_image_to_clip(
            image_path=branded_img,
            duration=scene_dur,
            output_path=dest_clip,
            camera_movement=cam_movement
        )

        return dest_clip
