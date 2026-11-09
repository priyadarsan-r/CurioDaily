"""
Kokoro TTS engine adapter using Kokoro ONNX.
Supports deep, commanding, realistic male character voices:
- am_fenrir: Deep, commanding, dramatic male voice
- am_onyx: Serious, authoritative baritone
- bm_george: Intellectual British documentary narrator
- bm_lewis: Sharp, measured academic tone
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
import soundfile as sf

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "assets" / "models" / "kokoro" / "kokoro-v1.0.onnx"
DEFAULT_VOICES_PATH = Path(__file__).resolve().parent.parent / "assets" / "models" / "kokoro" / "voices-v1.0.bin"


class KokoroEngine:
    def __init__(
        self,
        model_path: Optional[str | Path] = None,
        voices_path: Optional[str | Path] = None
    ):
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.voices_path = Path(voices_path) if voices_path else DEFAULT_VOICES_PATH
        self._kokoro = None
        self._is_available = self._init_engine()

    def _init_engine(self) -> bool:
        if not (self.model_path.exists() and self.voices_path.exists()):
            try:
                from scripts.download_models import ensure_models
                ensure_models()
            except Exception as e:
                logger.debug("Automatic model download skipped: %s", e)

        if not (self.model_path.exists() and self.voices_path.exists()):
            return False

        try:
            from kokoro_onnx import Kokoro
            self._kokoro = Kokoro(str(self.model_path), str(self.voices_path))
            return True
        except Exception as exc:
            logger.warning("Failed initializing Kokoro ONNX: %s", exc)
            return False

    def is_available(self) -> bool:
        return self._is_available and self._kokoro is not None

    def synthesize(self, text: str, output_path: Path, voice: str = "am_fenrir", speed: float = 1.0) -> bool:
        """
        Synthesize speech using Kokoro ONNX.
        voice: am_fenrir, am_onyx, bm_george, bm_lewis, am_adam, etc.
        """
        if not self.is_available():
            logger.info("Kokoro ONNX engine not available; falling back.")
            return False

        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            lang = "en-gb" if voice.startswith("b") else "en-us"

            samples, sample_rate = self._kokoro.create(
                text=text,
                voice=voice,
                speed=speed,
                lang=lang
            )
            sf.write(str(output_path), samples, sample_rate)
            return output_path.exists() and output_path.stat().st_size > 1000
        except Exception as exc:
            logger.warning("Kokoro ONNX synthesis error with voice %s: %s", voice, exc)
            return False
