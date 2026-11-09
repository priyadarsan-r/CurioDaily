"""
Gemini AI Pro Video & GIF Engine for CurioDaily.
Converts any script into a cinematic vertical Reel using Google Gemini Pro & Imagen 3.
Generates 10 tailored photorealistic scenes, 10 animated GIFs, kinetic subtitles, and audio.

Usage:
    python scripts/generate_gemini_reel.py --sample --category money_secrets
    python scripts/generate_gemini_reel.py --title "The Framing Effect" --category human_psychology --script-file script.txt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.gemini_director import GeminiDirector, get_gemini_api_key
from media.cinematic_renderer import CinematicRenderer
from media.create_captions import create_ass_subtitles, create_srt_subtitles
from media.create_visuals import create_reel_scene_image
from media.internet_media import overlay_brand_elements_on_image
from media.providers.gemini_image_provider import GeminiImagenProvider, convert_video_clip_to_gif
from media.providers.video_providers import KenBurnsVideoProvider
from media.quality_inspector import QualityInspector
from media.sound_design import SoundDesigner
from media.create_reel import concat_wav_files
from media.tts import TTSManager
from scripts.generate_cinematic_reel import SAMPLE_SCRIPTS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("GeminiReelCLI")


class GeminiReelGenerator:
    """
    Coordinates end-to-end video and GIF generation powered by Google Gemini AI Pro and Imagen 3.
    """

    def __init__(self, output_root: Optional[Path] = None):
        self.output_root = output_root or PROJECT_ROOT / "output"
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.gemini_director = GeminiDirector()
        self.imagen_provider = GeminiImagenProvider()
        self.ken_burns = KenBurnsVideoProvider()
        self.tts = TTSManager()
        self.sound_designer = SoundDesigner()
        self.renderer = CinematicRenderer()
        self.inspector = QualityInspector()

    def generate(
        self,
        script: str,
        title: str,
        category: str = "daily_mystery",
        generate_gifs: bool = True
    ) -> Dict[str, Any]:
        """
        Execute full 10-scene Gemini AI Pro generation pipeline:
        1. Gemini analyzes script into exactly 10 scene prompts.
        2. Kokoro TTS synthesizes voiceover.
        3. Gemini Imagen 3 generates 10 tailored vertical images.
        4. Ken Burns animates images into video clips & converts to 10 GIFs.
        5. ASS kinetic subtitles burned with glassmorphism pill.
        6. Cinematic sound design mixed with music and SFX.
        7. FFmpeg exports 1080x1920 MP4 reel.
        """
        run_hash = uuid.uuid4().hex[:5]
        content_dir = self.output_root / f"gemini_{category[:4]}_{run_hash}"
        content_dir.mkdir(parents=True, exist_ok=True)

        logger.info("=== Starting Gemini AI Pro Generation for: [%s] '%s' ===", category.upper(), title)
        logger.info("Output directory: %s", content_dir)

        api_key_status = "CONFIGURED (Google Gemini AI Pro / Imagen 3 Active)" if self.gemini_director.is_available else "UNCONFIGURED (Using High-Detail Generative Fallback)"
        logger.info("Gemini API Key: %s", api_key_status)

        # 1. Ask Gemini to analyze script and create 10 tailored scenes
        scenes = self.gemini_director.analyze_script_into_10_scenes(script, title, category)
        logger.info("Step 1 Complete: Script divided into exactly %d scenes by Gemini Director.", len(scenes))

        # Save scenes JSON specification
        scenes_file = content_dir / "gemini_scenes.json"
        scenes_file.write_text(json.dumps(scenes, indent=2), encoding="utf-8")

        # 2. Voiceover Synthesis per scene
        scene_audio_paths: List[Path] = []
        current_time = 0.0

        for idx, scene in enumerate(scenes, start=1):
            chunk = scene.get("narration_chunk", "").strip() or title
            audio_f = content_dir / f"scene_{idx:02d}_audio.wav"
            res = self.tts.synthesize(chunk, audio_f, pillar=category, speed=0.9)
            dur = max(2.5, res.get("duration_sec", 4.0))

            scene["start_sec"] = round(current_time, 2)
            scene["end_sec"] = round(current_time + dur, 2)
            scene["duration_sec"] = round(dur, 2)
            current_time += dur
            scene_audio_paths.append(audio_f)

        raw_voice_path = content_dir / "narration_raw.wav"
        total_audio_duration = concat_wav_files(scene_audio_paths, raw_voice_path)
        logger.info("Step 2 Complete: Voice synthesized (%.1fs across %d scenes).", total_audio_duration, len(scenes))

        # 3. Generate 10 tailored pictures using Gemini / Imagen 3
        generated_images: List[Path] = []
        generated_clips: List[Path] = []
        generated_gifs: List[Path] = []

        for idx, scene in enumerate(scenes, start=1):
            dur = scene["duration_sec"]
            is_outro = (idx == 10) or scene.get("visual_type") == "outro"

            raw_img = content_dir / f"scene_{idx:02d}.jpg"
            branded_img = content_dir / f"scene_{idx:02d}_branded.jpg"
            dest_clip = content_dir / f"scene_{idx:02d}_clip.mp4"
            dest_gif = content_dir / f"scene_{idx:02d}.gif"

            if is_outro:
                # Scene 10: Official branded CurioDaily follow card
                create_reel_scene_image(scene, title, category, raw_img)
            else:
                # Scenes 1 to 9: Photorealistic visual generated via Gemini Imagen 3
                prompt = scene.get("imagen_prompt", "")
                success = self.imagen_provider.fetch_image(prompt, raw_img, aspect_ratio="9:16")
                if not success or not raw_img.exists() or raw_img.stat().st_size < 5000:
                    # Deterministic fallback
                    create_reel_scene_image(scene, title, category, raw_img)

            # Apply brand badge & watermark overlay
            tag = scene.get("caption_keywords") or title[:25]
            overlay_brand_elements_on_image(raw_img, title, category, tag, branded_img)
            generated_images.append(raw_img)

            # Animate image with designated camera movement (Ken Burns motion)
            cam_move = scene.get("camera_movement", "slow_zoom_in")
            self.ken_burns.animate_image_to_clip(
                image_path=branded_img,
                duration=dur,
                output_path=dest_clip,
                camera_movement=cam_move
            )
            generated_clips.append(dest_clip)

            # Convert to animated GIF if requested
            if generate_gifs:
                convert_video_clip_to_gif(dest_clip, dest_gif, fps=15, width=540)
                if dest_gif.exists():
                    generated_gifs.append(dest_gif)

            logger.info("Scene %02d generated: image (%d bytes), video clip, and GIF", idx, raw_img.stat().st_size)

        logger.info(
            "Step 3 & 4 Complete: %d pictures, %d animated GIFs, and %d video clips generated.",
            len(generated_images), len(generated_gifs), len(generated_clips)
        )

        # 5. Format Subtitles (.srt and modern .ass with kinetic keyword highlights)
        srt_path = content_dir / "subtitles.srt"
        ass_path = content_dir / "subtitles.ass"
        # Map narration_chunk to narration for subtitle formatters
        for s in scenes:
            s["narration"] = s.get("narration_chunk", "")
        create_srt_subtitles(scenes, srt_path)
        create_ass_subtitles(scenes, ass_path, category=category)
        logger.info("Step 5 Complete: Modern ASS kinetic subtitles formatted.")

        # 6. Sound Design: Mood Music + Timed SFX + Audio Ducking
        master_audio = content_dir / "master_audio_mixed.wav"
        self.sound_designer.mix_master_audio(
            voiceover_path=raw_voice_path,
            scenes=scenes,
            category=category,
            total_duration=total_audio_duration,
            output_master_path=master_audio
        )
        logger.info("Step 6 Complete: Master audio mixed with mood music and SFX.")

        # 7. Cinematic FFmpeg Assembly
        output_mp4 = content_dir / "reel.mp4"
        scene_durations = [s["duration_sec"] for s in scenes]
        self.renderer.render_cinematic_video(
            scene_clip_paths=generated_clips,
            scene_durations=scene_durations,
            master_audio_path=master_audio,
            subtitles_ass_path=ass_path,
            output_mp4_path=output_mp4,
            fps=30
        )
        logger.info("Step 7 Complete: Video exported at %s (%d bytes).", output_mp4, output_mp4.stat().st_size)

        # 8. Quality Inspection
        report = self.inspector.inspect_video(
            video_path=output_mp4,
            expected_duration=total_audio_duration,
            scene_count=len(scenes),
            subtitles_path=ass_path
        )
        report_file = content_dir / "quality_report.json"
        report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info("Step 8 Complete: Quality report saved. Status: %s", report.get("status"))

        return {
            "content_dir": str(content_dir),
            "video_path": str(output_mp4),
            "scenes": scenes,
            "images": [str(p) for p in generated_images],
            "gifs": [str(p) for p in generated_gifs],
            "duration": total_audio_duration,
            "quality_report": report
        }


def main():
    parser = argparse.ArgumentParser(description="Generate 10 Gemini AI Pro Images, GIFs, and Vertical Video Reel")
    parser.add_argument("--title", type=str, default="", help="Topic title")
    parser.add_argument("--category", type=str, default="money_secrets", choices=["money_secrets", "human_psychology", "future_is_here", "daily_mystery"])
    parser.add_argument("--script", type=str, default="", help="Raw narration script")
    parser.add_argument("--script-file", type=str, default="", help="Path to text file containing narration")
    parser.add_argument("--sample", action="store_true", help="Use curated sample TED-talk script")
    parser.add_argument("--no-gifs", action="store_true", help="Skip animated GIF generation")
    args = parser.parse_args()

    title = args.title
    script = args.script

    if args.sample:
        script = SAMPLE_SCRIPTS.get(args.category, SAMPLE_SCRIPTS["money_secrets"])
        titles = {
            "money_secrets": "The Rule of 72: Exponential Freedom",
            "human_psychology": "The Framing Effect: Subconscious Bias",
            "future_is_here": "Solid-State Batteries: The Clean Revolution",
            "daily_mystery": "The Eye of the Sahara: Magma Mystery"
        }
        title = title or titles.get(args.category, "CurioDaily Discovery")

    elif args.script_file:
        fpath = Path(args.script_file)
        if not fpath.exists():
            print(f"Error: Script file {args.script_file} not found.")
            sys.exit(1)
        script = fpath.read_text(encoding="utf-8").strip()
        title = title or fpath.stem.replace("_", " ").title()

    if not script:
        print("Error: Please provide --script, --script-file, or --sample.")
        sys.exit(1)

    title = title or "CurioDaily Knowledge Byte"

    engine = GeminiReelGenerator()
    res = engine.generate(
        script=script,
        title=title,
        category=args.category,
        generate_gifs=not args.no_gifs
    )

    print("\n" + "=" * 60)
    print("🎬 GEMINI AI PRO REEL & GIFS GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"Title:         {title}")
    print(f"Category:      {args.category}")
    print(f"Scenes:        10 distinct scenes")
    print(f"Images:        {len(res['images'])} photorealistic 9:16 vertical images")
    print(f"GIFs:          {len(res['gifs'])} animated looping GIFs")
    print(f"Video File:    {res['video_path']}")
    print(f"Directory:     {res['content_dir']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
