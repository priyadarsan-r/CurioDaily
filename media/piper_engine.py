"""
Piper TTS engine adapter.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PiperEngine:
    def __init__(self, piper_bin: Optional[str] = None, model_path: Optional[str] = None):
        self.piper_bin = piper_bin or shutil.which("piper")
        self.model_path = model_path
        self._is_available = bool(self.piper_bin and Path(self.piper_bin).exists() and self.model_path and Path(self.model_path).exists())

    def is_available(self) -> bool:
        return self._is_available

    def synthesize(self, text: str, output_path: Path) -> bool:
        if not self._is_available:
            return False

        try:
            cmd = [
                self.piper_bin,
                "--model", self.model_path,
                "--output_file", str(output_path),
            ]
            proc = subprocess.run(cmd, input=text, text=True, capture_output=True, timeout=60)
            return proc.returncode == 0 and output_path.exists()
        except Exception as exc:
            logger.warning("Piper synthesis error: %s", exc)
            return False
