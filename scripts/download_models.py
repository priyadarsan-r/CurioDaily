"""
Download Kokoro ONNX model and voices file for zero-budget TTS narration.
Used in local setups and GitHub Actions CI/CD workflows.
"""

from __future__ import annotations

import logging
import sys
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DownloadModels")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "assets" / "models" / "kokoro"

MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

def download_file(url: str, dest_path: Path) -> bool:
    if dest_path.exists() and dest_path.stat().st_size > 1000000:
        logger.info(f"Model file already exists: {dest_path} ({dest_path.stat().st_size:,} bytes)")
        return True

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(".tmp")
    logger.info(f"Downloading {url} to {dest_path}...")

    try:
        urllib.request.urlretrieve(url, temp_path)
        temp_path.replace(dest_path)
        logger.info(f"Successfully downloaded {dest_path.name} ({dest_path.stat().st_size:,} bytes)")
        return True
    except Exception as exc:
        if temp_path.exists():
            temp_path.unlink()
        logger.error(f"Failed to download {url}: {exc}")
        return False

def ensure_models() -> bool:
    onnx_dest = MODELS_DIR / "kokoro-v1.0.onnx"
    voices_dest = MODELS_DIR / "voices-v1.0.bin"

    ok1 = download_file(MODEL_URL, onnx_dest)
    ok2 = download_file(VOICES_URL, voices_dest)
    return ok1 and ok2

if __name__ == "__main__":
    success = ensure_models()
    sys.exit(0 if success else 1)
