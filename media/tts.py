"""
Unified Text-to-Speech (TTS) manager with Kokoro, Piper, and zero-dependency fallback.
"""

from __future__ import annotations

import logging
import math
import os
import re
import struct
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional

from media.kokoro_engine import KokoroEngine
from media.piper_engine import PiperEngine

logger = logging.getLogger(__name__)

# Pronunciation mappings for currency, abbreviations, and acronyms
PRONUNCIATION_MAP = {
    r"\$([0-9,.]+)\s*([bB]illion|[bB])\b": r"\1 billion dollars",
    r"\$([0-9,.]+)\s*([mM]illion|[mM])\b": r"\1 million dollars",
    r"\$([0-9,.]+)\s*([kK])\b": r"\1 thousand dollars",
    r"\$([0-9,.]+)": r"\1 dollars",
    r"₹([0-9,.]+)\s*crore": r"\1 crore rupees",
    r"₹([0-9,.]+)\s*lakh": r"\1 lakh rupees",
    r"₹([0-9,.]+)": r"\1 rupees",
    r"€([0-9,.]+)": r"\1 euros",
    r"£([0-9,.]+)": r"\1 pounds",
    r"([0-9]+)%": r"\1 percent",
    r"\b([0-9]+)x\b": r"\1 times",
    r"\be\.g\.,?\b": "for example",
    r"\bi\.e\.,?\b": "that is",
    r"\bvs\.\b": "versus",
    r"\betc\.\b": "and so on",
    r"\bNASA\b": "Nasa",
    r"\bAI\b": "A.I.",
    r"\bEVs\b": "E.V.s",
    r"\bEV\b": "E.V.",
    r"\bCO2\b": "C.O.2",
}


def normalize_narration_text(text: str) -> str:
    """
    Expands currency, percentages, acronyms, and common abbreviations
    into natural spoken English for the TTS engine.
    """
    normalized = text
    for pattern, replacement in PRONUNCIATION_MAP.items():
        normalized = re.sub(pattern, replacement, normalized)
    return " ".join(normalized.split())


def generate_windows_sapi_wav(text: str, output_path: Path) -> bool:
    """
    Generate real, natural spoken audio using Windows built-in SAPI speech synthesizer.
    Runs 100% locally and offline with zero extra dependencies on Windows.
    """
    if sys.platform != "win32":
        return False
    try:
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ps_file = output_path.parent / f"_sapi_{output_path.stem}.ps1"
        safe_path = str(output_path).replace("\\", "/")
        clean_text = text.replace("'", "''")

        script = f"""
$voice = New-Object -ComObject SAPI.SpVoice
$stream = New-Object -ComObject SAPI.SpFileStream
$stream.Open('{safe_path}', 3, $false)
$voice.AudioOutputStream = $stream
$voice.Speak('{clean_text}')
$stream.Close()
"""
        ps_file.write_text(script, encoding="utf-8")
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_file.resolve())],
            capture_output=True,
            text=True,
            timeout=45
        )
        if ps_file.exists():
            try:
                ps_file.unlink()
            except Exception:
                pass

        return res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000
    except Exception as exc:
        logger.warning("Windows SAPI synthesis error: %s", exc)
        return False


def generate_synthesized_wav(
    text: str,
    output_path: Path,
    words_per_minute: int = 145,
    sample_rate: int = 44100
) -> float:
    """
    Zero-dependency deterministic audio generator that produces a valid PCM 16-bit WAV file.
    Calculates duration based on word count (145 WPM is standard natural narration pace).
    Provides realistic modulated audio suitable for video timeline alignment and test rendering.
    """
    words = text.split()
    word_count = max(1, len(words))
    # Duration in seconds based on narration pace
    duration = max(2.5, (word_count / words_per_minute) * 60.0)

    num_samples = int(duration * sample_rate)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Generate smooth modulated audio (voice-like harmonics between 160Hz and 320Hz)
        frames = bytearray()
        for i in range(num_samples):
            t = float(i) / sample_rate
            # Voice pitch modulation
            base_freq = 180.0 + 40.0 * math.sin(2.0 * math.pi * 0.5 * t)
            # Syllable cadence envelope
            envelope = 0.5 + 0.5 * math.sin(2.0 * math.pi * 3.5 * t)
            sample_val = int(envelope * 8000.0 * math.sin(2.0 * math.pi * base_freq * t))
            # Clamp to 16-bit signed integer range
            sample_val = max(-32767, min(32767, sample_val))
            frames.extend(struct.pack("<h", sample_val))

        wav_file.writeframes(frames)

    return duration


# Mapping of pillars to bold, commanding, realistic Kokoro male presets:
PILLAR_VOICES = {
    "money_secrets": "am_onyx",       # Serious, authoritative baritone
    "human_psychology": "bm_lewis",   # Sharp, measured academic tone
    "future_is_here": "am_fenrir",    # Deep, commanding, futuristic male voice
    "daily_mystery": "am_fenrir",     # Deep, dramatic documentary baritone
}


class TTSManager:
    def __init__(
        self,
        kokoro_model: Optional[str] = None,
        piper_bin: Optional[str] = None,
        piper_model: Optional[str] = None
    ):
        self.kokoro = KokoroEngine(kokoro_model)
        self.piper = PiperEngine(piper_bin, piper_model)

    def synthesize(
        self,
        text: str,
        output_path: Path,
        voice: str = "am_fenrir",
        pillar: Optional[str] = None,
        speed: float = 1.0
    ) -> Dict[str, Any]:
        """
        Synthesize speech from text.
        Applies pronunciation normalization, prioritizes Kokoro ONNX deep male voices,
        falls back to Windows SAPI / Piper, and lastly deterministic synthesizer.
        Returns duration and file path.
        """
        normalized_text = normalize_narration_text(text)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if pillar and pillar in PILLAR_VOICES:
            voice = PILLAR_VOICES[pillar]

        engine_used = "fallback_synth"
        duration = 0.0

        if self.kokoro.is_available():
            if self.kokoro.synthesize(normalized_text, output_path, voice=voice, speed=speed):
                engine_used = f"kokoro_{voice}"

        if engine_used == "fallback_synth" and self.piper.is_available():
            if self.piper.synthesize(normalized_text, output_path):
                engine_used = "piper"

        if engine_used == "fallback_synth" and sys.platform == "win32":
            if generate_windows_sapi_wav(normalized_text, output_path):
                engine_used = "windows_sapi"

        if engine_used == "fallback_synth":
            duration = generate_synthesized_wav(normalized_text, output_path)
        else:
            # Measure duration of created wav
            try:
                with wave.open(str(output_path), "rb") as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration = frames / float(rate)
            except Exception:
                duration = len(normalized_text.split()) / 2.4

        return {
            "output_path": str(output_path),
            "engine": engine_used,
            "voice": voice,
            "duration_sec": round(duration, 2),
            "word_count": len(normalized_text.split()),
        }
