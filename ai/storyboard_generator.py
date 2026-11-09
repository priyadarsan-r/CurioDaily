"""
Storyboard generator for 9:16 vertical Reels.
Converts script segments into structured 6-8 scene instructions with timing,
camera motion, visual descriptions, and on-screen text overlays.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def generate_reel_storyboard(reel_script: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate 6 storyboard scenes aligned with the 5 script sections:
    Hook, Context, Development (split into 2 scenes), Payoff, Close.
    Total duration targets 45-55 seconds.
    """
    category = reel_script.get("category", "daily_mystery")
    hook = reel_script.get("hook", "")
    context = reel_script.get("context", "")
    development = reel_script.get("development", "")
    payoff = reel_script.get("payoff", "")
    close = reel_script.get("close", "")

    # Split development if long
    dev_words = development.split()
    mid = len(dev_words) // 2
    dev1 = " ".join(dev_words[:mid])
    dev2 = " ".join(dev_words[mid:])

    scenes = [
        {
            "scene_number": 1,
            "section": "hook",
            "start_sec": 0.0,
            "end_sec": 4.0,
            "duration_sec": 4.0,
            "narration": hook,
            "visual_type": "title_card",
            "visual_description": f"High contrast kinetic title card with {category} theme badge.",
            "camera_effect": "zoom_in",
            "on_screen_text": reel_script.get("title", "").upper()[:40],
            "transition": "cut",
        },
        {
            "scene_number": 2,
            "section": "context",
            "start_sec": 4.0,
            "end_sec": 12.0,
            "duration_sec": 8.0,
            "narration": context,
            "visual_type": "motion_graphic",
            "visual_description": "Clean animated conceptual diagram illustrating the underlying problem.",
            "camera_effect": "pan_up",
            "on_screen_text": "THE HIDDEN PATTERN",
            "transition": "fade",
        },
        {
            "scene_number": 3,
            "section": "development_part1",
            "start_sec": 12.0,
            "end_sec": 23.0,
            "duration_sec": 11.0,
            "narration": dev1,
            "visual_type": "data_chart",
            "visual_description": "Visualizing concrete evidence and measured data points.",
            "camera_effect": "ken_burns",
            "on_screen_text": "HOW IT ACTUALLY WORKS",
            "transition": "fade",
        },
        {
            "scene_number": 4,
            "section": "development_part2",
            "start_sec": 23.0,
            "end_sec": 35.0,
            "duration_sec": 12.0,
            "narration": dev2,
            "visual_type": "evidence_showcase",
            "visual_description": "Focusing on the pivotal scientific finding or exponential curve.",
            "camera_effect": "zoom_in",
            "on_screen_text": "THE SCIENTIFIC DATA",
            "transition": "slide_left",
        },
        {
            "scene_number": 5,
            "section": "payoff",
            "start_sec": 35.0,
            "end_sec": 46.0,
            "duration_sec": 11.0,
            "narration": payoff,
            "visual_type": "reveal",
            "visual_description": "Highlighted golden rule or key mental model card.",
            "camera_effect": "subtle_pulse",
            "on_screen_text": "THE CORE TAKEAWAY",
            "transition": "fade",
        },
        {
            "scene_number": 6,
            "section": "close",
            "start_sec": 46.0,
            "end_sec": 52.0,
            "duration_sec": 6.0,
            "narration": close,
            "visual_type": "takeaway",
            "visual_description": "Thought-provoking takeaway question highlighting the core lesson.",
            "camera_effect": "zoom_in",
            "on_screen_text": "WHAT DO YOU THINK?",
            "transition": "fade",
        },
    ]

    return scenes
