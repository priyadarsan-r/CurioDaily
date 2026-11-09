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
            "You are an elite cinematic short-film director and visual storyteller for vertical cinema (Instagram Reels, YouTube Shorts).\n"
            f"Topic: \"{topic_title}\"\n"
            f"Category Pillar: \"{category}\"\n"
            "Below is a 1-minute narration script:\n"
            "--------------------------------------------------\n"
            f"{script}\n"
            "--------------------------------------------------\n"
            "DIRECT THIS AS A DRAMATIC SHORT MOVIE ALIGNED WITH THE SCRIPT:\n"
            "Divide the script into EXACTLY 10 chronological visual scenes (scenes 1 to 10).\n"
            "CRITICAL CINEMATOGRAPHY REQUIREMENTS:\n"
            "1. NO plain color gradients, NO abstract backgrounds, NO text cards, and NO 2D diagrams/charts.\n"
            "2. EVERY SCENE MUST FEATURE REAL-WORLD CINEMATIC SUBJECTS:\n"
            "   - REAL PEOPLE IN ACTION: characters walking, discussing, arguing intensely, reacting with shock, performing skits, gesturing over physical objects, working in high-stakes environments, or making decisions.\n"
            "   - PHYSICAL REALIA: stacks of crisp hundred-dollar bills, antique bank vaults, luxury skyscraper boardrooms, sleek electric vehicles, supersonic aircraft, cleanroom laboratories, robotics, quantum computers, exotic wildlife, desert sands, ancient ruins, or astronauts in deep space.\n"
            "3. PROFESSIONAL CREW DIRECTED SHOTS: Specify exact cinematography angles (e.g. dramatic medium two-shot, over-the-shoulder reaction shot, low-angle tracking shot, macro shallow focus, wide cinematic establishing shot), professional lighting (volumetric rim light, golden hour sun flare, moody rain-slicked neon reflection, dramatic chiaroscuro), 35mm film grain, shot on Panavision/Arri 8K.\n"
            "4. Dynamic narrative pacing: change the visual every 3-5 seconds to maintain peak viewer engagement.\n\n"
            "For each scene, output a JSON object with:\n"
            "  \"scene_number\": integer from 1 to 10\n"
            "  \"narration_chunk\": exact spoken words for this scene\n"
            "  \"visual_description\": 1-sentence description of the live-action short movie scene\n"
            "  \"imagen_prompt\": hyper-detailed, photorealistic prompt for Google Imagen 3 (e.g. 'Award-winning 35mm cinematic photograph, vertical 9:16, medium shot of two diverse business partners intensely debating over a tabletop with physical cash stacks and blueprints in a sunlit industrial loft, authentic emotional expressions, cinematic depth of field, shallow focus, natural golden hour lighting, f/1.8, 8k resolution, photorealistic, no text, no watermark')\n"
            "  \"camera_movement\": one of [\"slow_zoom_in\", \"slow_zoom_out\", \"slow_pan_right\", \"slow_pan_left\", \"rapid_push_in\"]\n"
            "  \"caption_keywords\": 2-4 uppercase bold words for kinetic on-screen subtitles\n"
            "  \"sound_effect\": one of [\"cinematic_impact\", \"whoosh_transition\", \"reveal_hit\", \"ambient_drone\"]\n"
            "  \"visual_type\": \"cinematic_scene\"\n\n"
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
                "visual_type": "cinematic_scene"
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

        words = cleaned.split()
        total_words = len(words)
        chunk_size = max(4, total_words // 10)

        scenes: List[Dict[str, Any]] = []
        i = 0
        camera_moves = ["rapid_push_in", "slow_zoom_in", "slow_pan_right", "slow_zoom_out", "slow_pan_left", "rapid_push_in", "slow_zoom_in", "slow_pan_right", "slow_zoom_in", "slow_zoom_in"]
        sfx_list = ["cinematic_impact", "whoosh_transition", "ambient_drone", "whoosh_transition", "ambient_drone", "whoosh_transition", "reveal_hit", "whoosh_transition", "reveal_hit", "reveal_hit"]

        pillar_visual_styles = {
            "money_secrets": [
                "Cinematic medium two-shot, 35mm film photograph, two diverse professional colleagues in their 30s walking side-by-side down a sunny urban financial avenue, one animatedly pointing at a tablet calculation while the other reacts with shock and realization, natural sunlight, f/1.8 depth of field",
                "Dramatic over-the-shoulder cinema shot of two business partners in a modern loft office passionately arguing over a wooden table covered with physical hundred-dollar cash stacks and financial contracts, dynamic gestures, cinematic rim lighting",
                "Medium tracking shot of a Wall Street floor trader in a tailored suit walking briskly through a bustling trading floor, shouting a trade while holding paperwork, chaotic background of traders reacting to glowing stock tickers, movie cinematography",
                "Close-up detailed cinema shot of a person's hands carefully stacking crisp hundred-dollar bills and polished gold bullion bars into an open vintage leather briefcase on dark marble, dramatic side light",
                "Emotional cinematic scene of a silver-haired grandfather sitting on a park bench under a sunlit oak tree teaching his young adult granddaughter, showing an antique gold pocket watch, genuine expressions of mentorship, Kodak Portra film",
                "Cinematic wide shot of an entrepreneur stepping out of a sleek luxury electric sedan in front of a gleaming modern bank headquarters at dusk, rain-slicked pavement reflecting neon city lights",
                "Medium shot of two fintech engineers in high-tech laboratory standing in front of transparent glass monitors, pointing and debating an exponential growth curve model, cinematic cyan atmospheric depth",
                "Intimate cinematic portrait of an investor sitting late at night at an executive mahogany desk, gazing through a floor-to-ceiling glass window at the glowing city skyline with thoughtful smile, warm desk lamp glow",
                "Macro cinema shot of human hands interacting with an intricate mechanical brass clockwork machine, spinning antique gear wheels and cascading gold coins, shallow focus, film noir lighting",
                "Cinematic low-angle tracking shot of a happy couple walking freely hand-in-hand along a breathtaking sun-drenched coastal cliff path, wind in their hair, pure financial freedom, film camera ending"
            ],
            "human_psychology": [
                "Cinematic medium two-shot of a doctor in a white coat sitting across from an anxious patient in a modern sunlit medical office, gesturing as he explains a critical health choice, authentic psychological tension, 35mm film",
                "Dramatic cinema shot of two business executives intensely arguing in a glass boardroom, one standing and slamming hands on table while other leans back calmly, raw human emotion, cinematic side lighting",
                "Street performance skit scene: a charismatic street magician in a crowded European plaza captivating a diverse crowd of onlookers with shocked, delighted facial expressions, natural golden hour sunlight",
                "Cinematic profile shot of a woman walking alone through a rainy neon-lit city crosswalk, holding an umbrella, deep in thought, pedestrians blurred around her in motion, cinematic film still",
                "Macro cinema shot of a person's face split by a harsh light beam, one eye wide in fear and the other calm and calculating, visual metaphor for the framing effect, dramatic chiaroscuro",
                "Medium shot of a group of friends seated in a cozy restaurant menu debating meal choices with laughter and lively hand gestures, warm atmospheric lighting, genuine human chemistry",
                "Intriguing cinematic shot of a person standing between two floor-to-ceiling antique mirrors in an art gallery, seeing two contrasting reflections of themselves, surreal psychological documentary",
                "Cinematic over-the-shoulder shot of a behavioral researcher observing a volunteer through a one-way mirror in a modern psychology lab, noting reactions on a clipboard",
                "Close-up of two people's hands reaching for the same object on a table in hesitation, dramatic tension, shallow depth of field, natural lighting",
                "Cinematic wide shot of a solitary hiker reaching the peak of a majestic misty mountain at sunrise, arms outstretched taking a deep breath of fresh air, conquering subconscious doubt"
            ],
            "future_is_here": [
                "Cinematic medium two-shot of two aerospace engineers in high-tech cleanroom jumpsuits intensely debating over a glowing solid-state battery prototype on an anti-static table, volumetric cyan light",
                "Dynamic tracking shot of a test driver in a sleek futuristic electric concept vehicle speeding across a salt flat at sunrise, dramatic dust trail, cinematic wide angle, commercial grade",
                "Two robotics technicians working together with tools calibrating a massive industrial robotic arm in an advanced gigafactory, sparks flying, authentic high-stakes industrial action",
                "Astronaut in spacesuit floating inside a space station cupola module, reaching out towards the glowing curved horizon of Earth, hyper-realistic documentary cinema, 35mm film",
                "Test pilot in flight suit walking confidently across a sunrise tarmac towards a sleek supersonic aircraft, ground crew in background, cinematic lens flare, top gun style",
                "Close-up of a bio-engineer's gloved hands holding an ultra-thin flexible transparent microchip that illuminates with electric blue circuits, pristine laboratory lighting",
                "Two smart-city urban planners standing on a high skyscraper balcony at twilight pointing tablets toward an autonomous electric drone fleet flying above the skyline",
                "Scientist in protective eyewear smiling with excitement as a laser-induced clean fusion reaction sparks in a vacuum chamber, dramatic neon reflections",
                "Wild deer grazing peacefully in a lush green valley directly beside a silent, emission-free modern geothermal energy plant, nature and clean technology harmony",
                "Cinematic group shot of a diverse team of young scientists cheering and embracing in a mission control room as monitors display breakthrough test results, pure emotional victory"
            ],
            "daily_mystery": [
                "Cinematic medium shot of two rugged geologists in khaki field gear kneeling in the Sahara desert sands, intensely arguing over a cracked ancient stone while pointing toward the horizon next to a vintage 4x4 Land Cruiser",
                "Dramatic shot of an expedition team walking through a swirling desert dust storm, wearing goggles and keffiyehs, discovering massive circular stone ridges rising from the dunes",
                "Two archaeologists inside a subterranean cavern, using soft brushes to uncover an ancient glowing crystalline relic buried beneath volcanic ash, torchlight flickering on cavern walls",
                "Cinematic tracking shot of an astronomer climbing an iron spiral staircase inside a massive vintage observatory dome, adjusting the giant brass telescope towards the starry night sky",
                "Over-the-shoulder shot of an astronaut through the space station window pointing camera down at the giant bullseye of the Eye of the Sahara, Earth glowing below",
                "Expedition research boat cutting through pitch-black arctic waters at night, scientists on deck aiming powerful searchlights into the foggy abyss, mysterious bioluminescence below",
                "Two hikers standing on the edge of a massive mist-filled prehistoric canyon, one pointing at bizarre concentric rock formations while the other checks a compass, epic cinematic scale",
                "Close-up of an explorer's weathered hands holding a brass pocket compass spinning erratically near an ancient magnetic meteorite, dramatic campfire glow",
                "Cinematic scene of a desert nomad with a camel standing motionless on a sand dune under a breathtaking canopy of the Milky Way, mysterious ancient atmosphere",
                "Cinematic wide shot of the research team packing their vehicles and driving into the golden sunrise across the vast desert plain, unanswered questions lingering, epic movie ending"
            ]
        }

        default_prompts = pillar_visual_styles.get(category, pillar_visual_styles["daily_mystery"])

        for idx in range(1, 11):
            start_word = (idx - 1) * chunk_size
            end_word = total_words if idx == 10 else min(total_words, idx * chunk_size)
            chunk = " ".join(words[start_word:end_word]) if start_word < total_words else f"Scene {idx}"

            prompt = default_prompts[(idx - 1) % len(default_prompts)]
            
            # Extract caption keywords
            clean_chunk = re.sub(r"[^a-zA-Z0-9\s]", "", chunk)
            chunk_w = [w.upper() for w in clean_chunk.split() if len(w) > 3]
            caption = " ".join(chunk_w[:3]) if chunk_w else topic_title[:20].upper()

            scenes.append({
                "scene_number": idx,
                "narration_chunk": chunk,
                "visual_description": f"Scene {idx} for {topic_title}",
                "imagen_prompt": prompt,
                "camera_movement": camera_moves[(idx - 1) % len(camera_moves)],
                "caption_keywords": caption,
                "sound_effect": sfx_list[(idx - 1) % len(sfx_list)],
                "visual_type": "cinematic_scene"
            })

        return scenes
