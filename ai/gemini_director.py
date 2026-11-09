"""
Gemini AI Pro Director: Analyzes 1-minute narration scripts using Google Gemini
and generates 10 tailored, photorealistic scene visual prompts for vertical video.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger(__name__)


def load_env_file() -> None:
    """Load environment variables from .env if present."""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and not os.getenv(k):
                            os.environ[k] = v
        except Exception as exc:
            logger.debug("Failed loading .env: %s", exc)


def get_gemini_api_key() -> str:
    """Retrieve Gemini / Google AI API key from environment."""
    load_env_file()
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""


class GeminiDirector:
    """
    Directs visual storytelling using Google Gemini Pro/Flash models.
    Breaks a script into exactly 10 distinct, cinematic visual scenes.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_gemini_api_key()

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def analyze_script_into_10_scenes(
        self,
        script: str,
        topic_title: str,
        category: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze script and generate exactly 10 distinct scenes with Imagen 3 prompts.
        Uses Google Gemini API if key is available, with intelligent deterministic fallback.
        """
        if self.is_available:
            try:
                scenes = self._call_gemini_for_10_scenes(script, topic_title, category)
                if scenes and len(scenes) == 10:
                    logger.info("Successfully received 10 tailored visual scenes from Gemini Pro.")
                    return scenes
            except Exception as exc:
                logger.warning("Gemini API call failed (%s). Using fallback scene generation.", exc)

        return self._fallback_10_scenes(script, topic_title, category)

    def _call_gemini_for_10_scenes(
        self,
        script: str,
        topic_title: str,
        category: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Call Google Gemini 2.0 Flash / 1.5 Flash via REST API with JSON response format."""
        # Primary models as instructed by user: gemini-3.6-flash
        models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
        
        prompt_instruction = (
            "You are a master cinematic video director and retention specialist for Instagram Reels and YouTube Shorts.\n"
            f"Topic: \"{topic_title}\"\n"
            f"Category Pillar: \"{category}\"\n"
            "Below is a 1-minute educational narration script:\n"
            "--------------------------------------------------\n"
            f"{script}\n"
            "--------------------------------------------------\n"
            "Your task is to divide this script into EXACTLY 10 chronological visual scenes (scenes 1 to 10).\n"
            "Every single scene MUST have a unique, highly specific visual that changes every 4-6 seconds to maintain extreme viewer retention.\n"
            "Avoid generic graphics, charts, or text diagrams. Every scene must be a breathtaking photograph or cinematic scene.\n\n"
            "For each scene, output a JSON object with:\n"
            "  \"scene_number\": integer from 1 to 10\n"
            "  \"narration_chunk\": exact spoken words for this scene\n"
            "  \"visual_description\": 1-sentence visual concept\n"
            "  \"imagen_prompt\": hyper-detailed, photorealistic prompt optimized for Google Imagen 3 (9:16 vertical portrait documentary photograph, 8k, award-winning cinematography, ultra-detailed textures, volumetric lighting, atmospheric depth, no watermarks, no text overlay)\n"
            "  \"camera_movement\": one of [\"slow_zoom_in\", \"slow_zoom_out\", \"slow_pan_right\", \"slow_pan_left\", \"rapid_push_in\"]\n"
            "  \"caption_keywords\": 2-4 uppercase bold words for kinetic on-screen subtitles\n"
            "  \"sound_effect\": one of [\"cinematic_impact\", \"whoosh_transition\", \"reveal_hit\", \"ambient_drone\"]\n"
            "  \"visual_type\": \"cinematic_scene\" for scenes 1-9, and \"outro\" for scene 10\n\n"
            "Return strictly a raw JSON array containing exactly 10 scene objects."
        )

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt_instruction}]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "responseMimeType": "application/json"
            }
        }

        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=20.0)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text_resp = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        # Parse JSON array
                        scenes = json.loads(text_resp)
                        if isinstance(scenes, list) and len(scenes) >= 8:
                            # Normalize to exactly 10
                            return self._normalize_scenes(scenes, script, topic_title, category)
                else:
                    logger.debug("Gemini model %s returned status %d: %s", model, resp.status_code, resp.text[:200])
            except Exception as exc:
                logger.debug("Failed requesting %s: %s", model, exc)

        return None

    def _normalize_scenes(
        self,
        scenes: List[Dict[str, Any]],
        script: str,
        topic_title: str,
        category: str
    ) -> List[Dict[str, Any]]:
        """Ensure scenes array has exactly 10 well-formed scene objects."""
        # Truncate or pad to exactly 10
        if len(scenes) > 10:
            scenes = scenes[:10]
        while len(scenes) < 10:
            idx = len(scenes) + 1
            scenes.append({
                "scene_number": idx,
                "narration_chunk": f"Key development {idx}",
                "visual_description": f"Cinematic perspective of {topic_title}",
                "imagen_prompt": f"cinematic 8k photorealistic documentary portrait 9:16 of {topic_title}, dramatic lighting, ultra-detailed",
                "camera_movement": "slow_zoom_in",
                "caption_keywords": topic_title[:20].upper(),
                "sound_effect": "whoosh_transition",
                "visual_type": "cinematic_scene" if idx < 10 else "outro"
            })

        for i, sc in enumerate(scenes, 1):
            sc["scene_number"] = i
            # Ensure caption_keywords is a clean uppercase string
            kw = sc.get("caption_keywords")
            if isinstance(kw, list):
                sc["caption_keywords"] = " ".join(str(w) for w in kw).upper()
            elif isinstance(kw, str):
                sc["caption_keywords"] = kw.upper()
            else:
                sc["caption_keywords"] = topic_title[:20].upper()

            if i == 10:
                sc["visual_type"] = "outro"
                if "follow" not in sc.get("narration_chunk", "").lower():
                    sc["narration_chunk"] = "If you like this, follow for daily tips on CurioDaily so you don't miss out."
                    sc["caption_keywords"] = "FOLLOW @CURIODAILY"
            else:
                sc["visual_type"] = "cinematic_scene"

        return scenes

    def _fallback_10_scenes(
        self,
        script: str,
        topic_title: str,
        category: str
    ) -> List[Dict[str, Any]]:
        """
        Deterministic rule-based division into exactly 10 scenes
        with high-end Imagen 3 prompts when offline or without API key.
        """
        cleaned = script.strip()
        cta_text = "If you like this, follow for daily tips on CurioDaily so you don't miss out."
        if cta_text.lower() not in cleaned.lower():
            cleaned = f"{cleaned} {cta_text}"

        words = cleaned.split()
        total_words = len(words)
        chunk_size = max(4, total_words // 10)

        scenes: List[Dict[str, Any]] = []
        i = 0
        camera_moves = ["rapid_push_in", "slow_zoom_in", "slow_pan_right", "slow_zoom_out", "slow_pan_left", "rapid_push_in", "slow_zoom_in", "slow_pan_right", "slow_zoom_in", "slow_zoom_in"]
        sfx_list = ["cinematic_impact", "whoosh_transition", "ambient_drone", "whoosh_transition", "ambient_drone", "whoosh_transition", "reveal_hit", "whoosh_transition", "reveal_hit", "reveal_hit"]

        pillar_visual_styles = {
            "money_secrets": [
                "Heavy solid steel vault door opening slowly in dark subterranean treasury, golden volumetric light beams, 8k documentary photograph",
                "Macro extreme close-up of intricate guilloche security patterns and metallic ink on uncirculated currency, cinematic shallow depth of field",
                "Wall Street trading floor at dawn with massive glowing green financial displays and shadowy trader silhouettes, anamorphic lens",
                "Gleaming stacks of pure 24-karat gold bullion bars on dark polished marble, reflection, dramatic rim lighting",
                "Antique brass pocket watch resting on financial ledger book, golden hour dust motes, philosophical time-is-money concept",
                "Modern luxury skyscraper glass penthouse overlooking sprawling financial district at twilight, neon accents",
                "High-tech digital mathematical calculation glowing holographic nodes hovering in dark laboratory, cinematic cyan depth",
                "Investor sitting quietly before multi-monitor Bloomberg terminal analyzing exponential growth curve, cinematic moody side-lighting",
                "Vintage brass mechanical hourglass with cascading white quartz sand, ultra-detailed macro photography",
                "CurioDaily official branded card, dark glassmorphism, glowing emerald and cyan rings, 8k luxury typography, follow call-to-action"
            ],
            "human_psychology": [
                "Intense dramatic portrait of human face emerging from deep shadow, dual lighting blue and amber, psychological depth, 8k documentary photograph",
                "Silhouetted human figure standing alone at the center of an infinite labyrinth of frosted glass doors, mysterious fog",
                "Microscopic neural synapse firing brilliant electric gold bio-luminescent pulse, dark matter backdrop, scientific realism",
                "Bystander crowd on bustling rain-slicked city crosswalk frozen in place while single individual looks up, cinematic motion blur",
                "Close-up of human eye with hyper-detailed iris reflecting an intricate decision tree, macro portrait",
                "Antique mirror showing two contrasting reflections of the same person, subtle cognitive dissonance, moody lighting",
                "Person standing on the edge of a dramatic misty coastal cliff at sunrise, contemplation, expansive cinematic wide shot",
                "Psychologist's vintage study with leather wingback chair, warm ambient lamp, ancient books, analytical atmosphere",
                "Brain hemisphere glowing with intricate bio-luminescent geometric neural pathways, dark luxury background",
                "CurioDaily official branded card, dark glassmorphism, glowing amethyst and cyan rings, 8k luxury typography, follow call-to-action"
            ],
            "future_is_here": [
                "Advanced solid-state ceramic battery cell glowing with neon cyan energy in cleanroom laboratory, 8k scientific photograph",
                "Futuristic electric supersonic aircraft banking through cloudscape at golden hour, ultra-realistic aerospace rendering",
                "Robotic precision manipulator arm assembling nanoscale quantum crystalline lattice, macro depth of field",
                "Massive fusion tokamak reactor core with swirling magnetic plasma torus, brilliant purple and cyan light",
                "Next-generation electric vehicle chassis showing glowing battery modules under carbon fiber body, futuristic showroom",
                "Clean energy mega-facility with sleek solar arrays and green hydrogen turbines stretching to mountain horizon",
                "Close-up of flexible transparent graphene semiconductor circuit integrated into human palm, bio-cybernetic realism",
                "Autonomous electric drone fleet navigating neon-lit smart city skyline at dusk, cinematic aerial perspective",
                "Scientist in cleanroom suit examining glowing crystalline energy substrate with holographic diagnostics, dramatic lighting",
                "CurioDaily official branded card, dark glassmorphism, glowing electric blue and violet rings, 8k luxury typography, follow call-to-action"
            ],
            "daily_mystery": [
                "Colossal Richat Structure Eye of the Sahara viewed from low Earth orbit, desert sands swirls, breathtaking satellite photograph",
                "Remote geological expedition team at sunset examining giant concentric quartzite rings in Mauritania desert, dust storm haze",
                "Massive ancient subterranean magma cavern with cooling volcanic basalt columns and glowing embers, dramatic lighting",
                "Deep space telescope view of distant enigmatic radio source pulsing against sea of spiral galaxies, James Webb style",
                "Astronaut in spacesuit tethered outside International Space Station gazing down at illuminated continent, ultra-realistic",
                "Ancient stone monoliths rising from dense primeval forest engulfed in morning mist, mysterious archaeological discovery",
                "Research vessel at night scanning the dark abyssal ocean depths with powerful underwater searchlights, bioluminescence",
                "Macro shot of ancient meteorite fragment showing extraterrestrial olivine crystals under polarized light, scientific discovery",
                "Radio astronomy observatory dish array under sweeping Milky Way galaxy night sky, long exposure",
                "CurioDaily official branded card, dark glassmorphism, glowing celestial cyan rings, 8k luxury typography, follow call-to-action"
            ]
        }

        default_prompts = pillar_visual_styles.get(category, pillar_visual_styles["daily_mystery"])

        for idx in range(1, 11):
            start_word = (idx - 1) * chunk_size
            end_word = total_words if idx == 10 else min(total_words, idx * chunk_size)
            chunk = " ".join(words[start_word:end_word]) if start_word < total_words else f"Scene {idx}"

            is_outro = (idx == 10)
            prompt = default_prompts[(idx - 1) % len(default_prompts)]
            
            # Extract caption keywords
            clean_chunk = re.sub(r"[^a-zA-Z0-9\s]", "", chunk)
            chunk_w = [w.upper() for w in clean_chunk.split() if len(w) > 3]
            caption = " ".join(chunk_w[:3]) if chunk_w else topic_title[:20].upper()
            if is_outro:
                caption = "FOLLOW @CURIODAILY"

            scenes.append({
                "scene_number": idx,
                "narration_chunk": chunk,
                "visual_description": f"Scene {idx} for {topic_title}",
                "imagen_prompt": prompt,
                "camera_movement": camera_moves[(idx - 1) % len(camera_moves)],
                "caption_keywords": caption,
                "sound_effect": sfx_list[(idx - 1) % len(sfx_list)],
                "visual_type": "outro" if is_outro else "cinematic_scene"
            })

        return scenes
