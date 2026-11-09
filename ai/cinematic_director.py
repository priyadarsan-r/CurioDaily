"""
Cinematic Director and Audience Retention Engine.
Converts a 1-minute narration script into 15-20 high-retention cinematic scenes
with precise camera direction, lighting, sound design cues, and AI generation prompts.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Cinematic vocabulary presets for retention-driven storytelling
CAMERA_ANGLES = ["extreme_close_up", "close_up", "medium_shot", "wide_aerial", "low_angle", "dutch_angle", "macro"]
CAMERA_MOVEMENTS = ["slow_zoom_in", "slow_pan_right", "rapid_push_in", "smooth_orbit", "tracking_forward", "tilt_up", "handheld_subtle"]
LIGHTINGS = [
    "dramatic chiaroscuro with deep shadows",
    "volumetric golden hour rays piercing through mist",
    "cold clinical neon with cyan accents",
    "moody atmospheric shadows with high contrast",
    "subtle rim lighting with dark background",
    "cinematic anamorphic lens flare"
]
SOUND_EFFECTS = ["cinematic_impact", "whoosh_transition", "sub_boom", "tension_riser", "clock_ticking", "ambient_drone", "reveal_hit"]
TRANSITIONS = ["cut", "whip_pan", "crossfade", "zoom_in_cut"]

RETENTION_STAGES = [
    {"name": "visual_hook", "min_sec": 0.0, "max_sec": 3.5, "target_cuts": 2},
    {"name": "curiosity_gap", "min_sec": 3.5, "max_sec": 10.0, "target_cuts": 3},
    {"name": "evidence_build", "min_sec": 10.0, "max_sec": 35.0, "target_cuts": 8},
    {"name": "twist_reveal", "min_sec": 35.0, "max_sec": 50.0, "target_cuts": 4},
    {"name": "conclusion_cta", "min_sec": 50.0, "max_sec": 65.0, "target_cuts": 3},
]


class CinematicDirector:
    """
    Directs scene breakdown, camera angles, lighting, sound effects, and AI prompts
    to convert a 1-minute script into 15-20 engaging 2-4s documentary scenes.
    """

    def __init__(self, llm_adapter: Optional[Any] = None):
        self.llm = llm_adapter

    def break_into_cinematic_scenes(
        self,
        script: str,
        topic_title: str = "",
        category: str = "daily_mystery",
        total_estimated_sec: float = 55.0
    ) -> List[Dict[str, Any]]:
        """
        Divide narration script into 15-20 scenes matching the 2-4s pacing.
        Assigns camera angle, lighting, sound effects, and AI generation prompt.
        """
        # Clean script into phrases/sentences (no forced branding/CTA injection)
        cleaned = script.strip()

        words = cleaned.split()
        total_words = len(words)
        if total_words == 0:
            return []

        # Target between 15 and 20 scenes (average 6-9 words per visual cut)
        target_scene_count = max(15, min(20, total_words // 7))
        chunk_size = max(5, round(total_words / target_scene_count))

        word_chunks: List[str] = []
        i = 0
        while i < total_words:
            end_idx = min(total_words, i + chunk_size)
            # Try to break on punctuation if nearby
            if end_idx < total_words:
                for lookahead in range(end_idx, min(total_words, end_idx + 3)):
                    if any(words[lookahead - 1].endswith(p) for p in [".", ",", "—", "!", "?"]):
                        end_idx = lookahead
                        break
            chunk = " ".join(words[i:end_idx])
            word_chunks.append(chunk)
            i = end_idx

        # Enforce exactly 15 to 20 scenes
        while len(word_chunks) < 15 and len(word_chunks) > 1:
            # Split the longest chunk
            longest_idx = max(range(len(word_chunks)), key=lambda idx: len(word_chunks[idx].split()))
            w = word_chunks[longest_idx].split()
            if len(w) <= 4:
                break
            half = len(w) // 2
            word_chunks[longest_idx] = " ".join(w[:half])
            word_chunks.insert(longest_idx + 1, " ".join(w[half:]))

        total_chunks = len(word_chunks)
        scenes: List[Dict[str, Any]] = []

        # Character-weighted duration allocation
        total_chars = max(1, sum(len(c) for c in word_chunks))
        curr_t = 0.0

        for idx, chunk in enumerate(word_chunks, start=1):
            dur = max(2.0, round(total_estimated_sec * (len(chunk) / total_chars), 2))
            start_t = round(curr_t, 2)
            end_t = round(start_t + dur, 2)
            curr_t = end_t

            # Stage detection based on temporal position
            pct = start_t / max(1.0, total_estimated_sec)
            if start_t <= 3.2:
                stage = "visual_hook"
                sfx = "cinematic_impact" if idx == 1 else "whoosh_transition"
                cam_movement = "rapid_push_in" if idx == 1 else "slow_zoom_in"
                cam_angle = "close_up" if idx == 1 else "extreme_close_up"
                trans = "cut"
            elif pct < 0.20:
                stage = "curiosity_gap"
                sfx = "clock_ticking" if idx % 2 == 0 else "ambient_drone"
                cam_movement = "slow_pan_right"
                cam_angle = "low_angle"
                trans = "crossfade"
            elif pct < 0.65:
                stage = "evidence_build"
                sfx = "whoosh_transition" if idx % 3 == 0 else "ambient_drone"
                cam_movement = CAMERA_MOVEMENTS[idx % len(CAMERA_MOVEMENTS)]
                cam_angle = CAMERA_ANGLES[idx % len(CAMERA_ANGLES)]
                trans = "whip_pan" if idx % 4 == 0 else "cut"
            elif pct < 0.85:
                stage = "twist_reveal"
                sfx = "reveal_hit" if "reveal" not in [s.get("sound_effect") for s in scenes[-2:]] else "sub_boom"
                cam_movement = "rapid_push_in"
                cam_angle = "extreme_close_up"
                trans = "zoom_in_cut"
            else:
                stage = "conclusion_cta"
                sfx = "whoosh_transition"
                cam_movement = "slow_zoom_in"
                cam_angle = "medium_shot"
                trans = "crossfade"

            lighting = LIGHTINGS[idx % len(LIGHTINGS)]

            # All scenes are pure cinematic visual documentary scenes (no branded outro cards)
            visual_type = "cinematic_scene"
            visual_desc = self._craft_visual_description(chunk, topic_title, category, stage)
            ai_prompt = self._craft_ai_prompt(chunk, topic_title, category, cam_angle, lighting, visual_desc)
            caption = self._extract_caption_keywords(chunk)

            scene_data = {
                "scene_number": idx,
                "start_sec": start_t,
                "end_sec": end_t,
                "duration_sec": dur,
                "narration": chunk,
                "visual_type": visual_type,
                "visual_description": visual_desc,
                "ai_prompt": ai_prompt,
                "camera_angle": cam_angle,
                "camera_movement": cam_movement,
                "lighting": lighting,
                "caption_text": caption,
                "sound_effect": sfx,
                "transition": trans,
                "retention_purpose": stage,
            }
            scenes.append(scene_data)

        logger.info(f"Generated {len(scenes)} cinematic scenes for '{topic_title}' (pacing: ~{total_estimated_sec/len(scenes):.1f}s/cut)")
        return scenes

    def _craft_visual_description(self, chunk: str, topic_title: str, category: str, stage: str) -> str:
        """Create a documentary-grade cinematic visual description for the scene."""
        keywords = [w.strip(".,—!?:;\"'") for w in chunk.split() if len(w) > 3]
        key_phrase = " ".join(keywords[:4]) if keywords else topic_title

        if stage == "visual_hook":
            return f"Shocking, high-contrast visual introducing {topic_title}: dramatic focus on {key_phrase}."
        elif stage == "curiosity_gap":
            return f"Mysterious cinematic perspective exploring the anomaly of {key_phrase} in {topic_title}."
        elif stage == "evidence_build":
            return f"Detailed documentary evidence showcase: realistic capture of {key_phrase} with scientific clarity."
        elif stage == "twist_reveal":
            return f"Pivotal breakthrough reveal: intense focus on the unexpected mechanism behind {key_phrase}."
        else:
            return f"Philosophical closing perspective synthesizing the broader meaning of {topic_title}."

    def _craft_ai_prompt(
        self,
        chunk: str,
        topic_title: str,
        category: str,
        cam_angle: str,
        lighting: str,
        visual_desc: str
    ) -> str:
        """Formulate a high-retention photorealistic AI video/image prompt."""
        category_styles = {
            "money_secrets": "hyper-realistic financial documentary cinematography, high-end macro details of wealth and currency, 35mm lens, corporate noir aesthetic",
            "human_psychology": "intense psychological documentary style, human emotional depth, photorealistic neural and cognitive visualization, cinematic 8k",
            "future_is_here": "photorealistic futuristic technology cinematography, ultra-detailed laboratory instrumentation, clean industrial aesthetics, IMAX clarity",
            "daily_mystery": "mysterious NatGeo documentary cinematography, dramatic archaeological and planetary exploration, photorealistic textures, atmospheric depth"
        }
        style = category_styles.get(category, category_styles["daily_mystery"])
        clean_angle = cam_angle.replace("_", " ")

        return (
            f"Cinematic {clean_angle} shot of {visual_desc}. "
            f"Subject: {topic_title}. "
            f"{style}. {lighting}. "
            f"Photorealistic 8k, highly detailed, masterwork color grading, vertical 9:16 composition, no blur, no text, no distortion."
        )

    def _extract_caption_keywords(self, chunk: str) -> str:
        """Extract 3-5 punchy words for kinetic on-screen caption display."""
        words = chunk.split()
        if len(words) <= 5:
            return " ".join(words).upper()
        # Take first 4-5 words
        return " ".join(words[:4]).upper()
