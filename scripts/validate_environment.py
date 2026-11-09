"""
Environment validation script.
Checks Python version, required packages, configuration files,
directory structure, FFmpeg, and optional credentials.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

REQUIRED_PACKAGES = [
    "requests",
    "httpx",
    "bs4",
    "feedparser",
    "PIL",
    "pytest",
    "yaml",
]

REQUIRED_CONFIGS = [
    "brand.yml",
    "quality.yml",
    "schedule.yml",
    "sources.yml",
    "topics.yml",
]

REQUIRED_DIRS = [
    "config",
    "discovery",
    "research",
    "ai",
    "media",
    "publishing",
    "analytics",
    "database",
    "output",
    "reports",
]


def validate_environment() -> bool:
    print("=== CurioDaily Environment Validation ===")
    all_ok = True

    # 1. Python Version
    py_version = sys.version_info
    if py_version.major == 3 and py_version.minor >= 10:
        print(f" [PASS] Python version: {sys.version.split()[0]} (>= 3.10 required)")
    else:
        print(f" [FAIL] Python version: {sys.version.split()[0]} (Requires Python 3.10+)")
        all_ok = False

    # 2. Required Packages
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
            print(f" [PASS] Package '{pkg}' is installed.")
        except ImportError:
            print(f" [FAIL] Package '{pkg}' is MISSING.")
            all_ok = False

    # 3. Required Directories
    root_dir = Path(__file__).resolve().parent.parent
    for d in REQUIRED_DIRS:
        d_path = root_dir / d
        if d_path.exists() and d_path.is_dir():
            print(f" [PASS] Directory '{d}/' exists.")
        else:
            d_path.mkdir(parents=True, exist_ok=True)
            print(f" [FIXED] Created directory '{d}/'.")

    # 4. Required Config Files
    for cfg in REQUIRED_CONFIGS:
        cfg_path = root_dir / "config" / cfg
        if cfg_path.exists():
            print(f" [PASS] Config file '{cfg}' exists.")
        else:
            print(f" [FAIL] Config file '{cfg}' is missing.")
            all_ok = False

    # 5. FFmpeg Check
    if shutil.which("ffmpeg"):
        print(" [PASS] FFmpeg is available in system PATH.")
    else:
        print(" [WARN] FFmpeg executable not found in PATH (Media will use mock/fallback mode unless installed).")

    # 6. Credentials Check
    ig_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
    ig_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    if ig_id and ig_token:
        print(" [PASS] Instagram credentials detected in environment variables.")
    else:
        print(" [INFO] Instagram credentials not configured. Running in local test / mock mode.")

    print("==========================================")
    if all_ok:
        print(" Environment validation PASSED.")
    else:
        print(" Environment validation FAILED with errors.")
    return all_ok


if __name__ == "__main__":
    success = validate_environment()
    sys.exit(0 if success else 1)
