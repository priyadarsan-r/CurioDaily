"""
Modular Local LLM and deterministic template fallback adapter.
Strictly zero-budget: no paid APIs, no subscriptions, fully local.
"""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMAdapter:
    """
    Adapter supporting local inference via llama.cpp if installed,
    or deterministic rule-based generation when running in standard CI/CD runners.
    """

    def __init__(
        self,
        llama_cli_path: Optional[str] = None,
        model_path: Optional[str] = None
    ):
        self.llama_cli_path = llama_cli_path or os.getenv("LLAMA_CLI_PATH")
        self.model_path = model_path or os.getenv("LLAMA_MODEL_PATH")
        self.has_local_llama = bool(
            self.llama_cli_path and
            self.model_path and
            os.path.exists(self.llama_cli_path) and
            os.path.exists(self.model_path)
        )

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Generate text using local model or fallback."""
        if self.has_local_llama:
            try:
                cmd = [
                    self.llama_cli_path,
                    "-m", self.model_path,
                    "-p", prompt,
                    "-n", str(max_tokens),
                    "--temp", str(temperature),
                    "-c", "2048",
                    "--silent-prompt"
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if proc.returncode == 0:
                    return proc.stdout.strip()
                logger.warning("Local llama.cpp exited with code %d: %s", proc.returncode, proc.stderr)
            except Exception as exc:
                logger.warning("Failed executing llama.cpp: %s. Using deterministic fallback.", exc)

        # Fallback will be handled at the script generation layer
        return ""
