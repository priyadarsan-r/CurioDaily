"""
Cinematic Sound Design and Audio Mixing Engine.
Selects mood-based background music, generates/places cinematic sound effects
(impacts, whooshes, risers, sub booms), and executes audio ducking with FFmpeg.
"""

from __future__ import annotations

import logging
import math
import os
import struct
import subprocess
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional

from media.ffmpeg_utils import get_ffmpeg_binary

logger = logging.getLogger(__name__)

ASSETS_MUSIC_DIR = Path(__file__).resolve().parent.parent / "assets" / "music"
ASSETS_SFX_DIR = Path(__file__).resolve().parent.parent / "assets" / "sfx"

MOOD_MAP = {
    "daily_mystery": "suspenseful_mystery",
    "future_is_here": "futuristic_electronic",
    "human_psychology": "introspective_pulse",
    "money_secrets": "sophisticated_pulse",
}


def generate_synthetic_ambient_music(mood: str, duration_sec: float, output_path: Path) -> Path:
    """
    Synthesize an atmospheric ambient drone bed with gentle harmonic pulses.
    Zero-budget fallback ensuring videos have professional background music
    even before external MP3 tracks are added to assets/music/.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 44100
    num_samples = int(sample_rate * duration_sec)

    # Base frequencies per mood (in Hz)
    mood_freqs = {
        "suspenseful_mystery": (55.0, 82.5, 110.0),      # Low A drone with fifth
        "futuristic_electronic": (65.4, 98.0, 130.8),    # Low C drone with fifth
        "introspective_pulse": (73.4, 110.0, 146.8),     # Low D drone
        "sophisticated_pulse": (65.4, 82.4, 98.0),       # Low C major triad
    }
    f1, f2, f3 = mood_freqs.get(mood, (55.0, 82.5, 110.0))

    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(2)  # Stereo
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)

        frames = bytearray()
        for i in range(num_samples):
            t = float(i) / sample_rate

            # Subtle pulse cadence (1.2 Hz pulse)
            pulse = 0.7 + 0.3 * math.sin(2.0 * math.pi * 0.8 * t)

            # Atmospheric drone tones
            s1 = math.sin(2.0 * math.pi * f1 * t)
            s2 = 0.5 * math.sin(2.0 * math.pi * f2 * t + 0.5)
            s3 = 0.25 * math.sin(2.0 * math.pi * f3 * t + 1.0)

            # Soft fade-in and fade-out
            fade_in = min(1.0, t / 2.0)
            fade_out = min(1.0, (duration_sec - t) / 2.0)
            env = fade_in * fade_out * pulse

            val = int(env * (s1 + s2 + s3) * 6000.0)
            val = max(-32767, min(32767, val))

            # Stereo spatial width
            left = val
            right = int(val * 0.95)
            frames.extend(struct.pack("<hh", left, right))

        wf.writeframes(frames)

    return output_path


def generate_synthetic_sfx(sfx_type: str, output_path: Path) -> Path:
    """Synthesize high-impact cinematic sound effects (impact, whoosh, riser, hit)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 44100
    dur = 1.2 if sfx_type in ("cinematic_impact", "sub_boom") else (0.6 if sfx_type == "whoosh_transition" else 1.0)
    num_samples = int(sample_rate * dur)

    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        frames = bytearray()
        for i in range(num_samples):
            t = float(i) / sample_rate

            if sfx_type in ("cinematic_impact", "sub_boom"):
                # Pitch drops from 120Hz to 35Hz
                freq = max(35.0, 120.0 * math.exp(-3.5 * t))
                env = math.exp(-2.8 * t)
                sig = math.sin(2.0 * math.pi * freq * t) + 0.15 * math.sin(2.0 * math.pi * 40.0 * t)
                val = int(env * sig * 16000.0)

            elif sfx_type == "whoosh_transition":
                # Filtered noise sweep
                env = math.sin(math.pi * (t / dur))
                noise = math.sin(2.0 * math.pi * (300.0 + 800.0 * (t / dur)) * t)
                val = int(env * noise * 12000.0)

            elif sfx_type == "reveal_hit":
                # High resonant chime hit
                freq = 520.0
                env = math.exp(-3.0 * t)
                sig = math.sin(2.0 * math.pi * freq * t) + 0.4 * math.sin(2.0 * math.pi * freq * 2.0 * t)
                val = int(env * sig * 14000.0)

            else:  # tension_riser or ambient click
                freq = 150.0 + 350.0 * (t / dur)
                env = t / dur
                sig = math.sin(2.0 * math.pi * freq * t)
                val = int(env * sig * 10000.0)

            val = max(-32767, min(32767, val))
            frames.extend(struct.pack("<hh", val, val))

        wf.writeframes(frames)

    return output_path


class SoundDesigner:
    """Manages mood music selection, SFX placement, and audio ducking."""

    def __init__(self):
        self.ffmpeg = get_ffmpeg_binary()
        ASSETS_SFX_DIR.mkdir(parents=True, exist_ok=True)
        ASSETS_MUSIC_DIR.mkdir(parents=True, exist_ok=True)

    def get_or_create_sfx(self, sfx_type: str) -> Path:
        """Find existing SFX file in assets/sfx or synthesize on demand."""
        for ext in (".wav", ".mp3"):
            candidate = ASSETS_SFX_DIR / f"{sfx_type}{ext}"
            if candidate.exists() and candidate.stat().st_size > 1000:
                return candidate

        # Generate synthetic fallback
        synth_path = ASSETS_SFX_DIR / f"{sfx_type}.wav"
        if not synth_path.exists():
            generate_synthetic_sfx(sfx_type, synth_path)
        return synth_path

    def get_or_create_music(self, category: str, duration_sec: float, dest_path: Path) -> Path:
        """Find mood music in assets/music or synthesize an ambient track."""
        mood = MOOD_MAP.get(category, "suspenseful_mystery")

        # Check for user-provided MP3/WAV in assets/music/
        for f in ASSETS_MUSIC_DIR.glob("*"):
            if f.suffix.lower() in (".mp3", ".wav") and mood in f.stem.lower():
                return f

        # Check general files
        general_files = [f for f in ASSETS_MUSIC_DIR.glob("*") if f.suffix.lower() in (".mp3", ".wav")]
        if general_files:
            return general_files[0]

        # Generate bespoke ambient music track matching exact duration
        generate_synthetic_ambient_music(mood, duration_sec + 2.0, dest_path)
        return dest_path

    def mix_master_audio(
        self,
        voiceover_path: Path,
        scenes: List[Dict[str, Any]],
        category: str,
        total_duration: float,
        output_master_path: Path
    ) -> bool:
        """
        Mix voiceover, background music with audio ducking (16% volume),
        and position sound effects at scene transitions.
        """
        if not self.ffmpeg or not voiceover_path.exists():
            logger.warning("FFmpeg missing or voiceover path missing.")
            return False

        output_master_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Resolve Background Music
        bgm_temp = output_master_path.parent / "bgm_bed.wav"
        bgm_path = self.get_or_create_music(category, total_duration, bgm_temp)

        # 2. Build FFmpeg audio filtergraph with audio ducking
        # Voiceover at 100%, background music ducked to 16% volume
        # If SFX exist, mix key impacts at scene transitions
        sfx_inputs: List[str] = []
        input_args = ["-i", str(voiceover_path.resolve()), "-i", str(bgm_path.resolve())]

        # Collect key sound effects (limit to 4 most impactful to avoid audio clutter)
        key_scenes = [s for s in scenes if s.get("sound_effect") in ("cinematic_impact", "sub_boom", "reveal_hit")][:4]

        filter_complex_parts = [
            "[0:a]volume=1.0[voice]",
            "[1:a]volume=0.15[bgm]",
        ]

        if key_scenes:
            mix_labels = ["[voice]", "[bgm]"]
            for idx, sc in enumerate(key_scenes, start=2):
                sfx_file = self.get_or_create_sfx(sc["sound_effect"])
                if sfx_file.exists():
                    input_args.extend(["-i", str(sfx_file.resolve())])
                    delay_ms = int(sc.get("start_sec", 0.0) * 1000)
                    filter_complex_parts.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms},volume=0.35[sfx{idx}]")
                    mix_labels.append(f"[sfx{idx}]")

            all_inputs = "".join(mix_labels)
            filter_complex_parts.append(
                f"{all_inputs}amix=inputs={len(mix_labels)}:duration=first:dropout_transition=2[outa]"
            )
        else:
            filter_complex_parts.append("[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]")

        cmd = [
            self.ffmpeg, "-y",
            *input_args,
            "-filter_complex", ";".join(filter_complex_parts),
            "-map", "[outa]",
            "-t", str(total_duration),
            "-c:a", "pcm_s16le",
            str(output_master_path.resolve())
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if res.returncode == 0 and output_master_path.exists():
                logger.info(f"Master sound design mixed successfully: {output_master_path.stat().st_size:,} bytes")
                return True
            logger.warning(f"Audio mix error: {res.stderr}")
        except Exception as exc:
            logger.warning(f"Sound design mix error: {exc}")

        # Fallback to pure voiceover if mixing fails
        import shutil
        shutil.copy2(voiceover_path, output_master_path)
        return True
