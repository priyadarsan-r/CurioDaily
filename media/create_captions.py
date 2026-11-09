"""
Caption and subtitle generator for vertical short-form video.
Produces both standard .srt and modern styled .ass formats with:
- Bold uppercase typography (Arial Black / Segoe UI)
- Translucent dark glassmorphism pill box (BorderStyle=3)
- Dynamic keyword and number highlights in vibrant pillar accent colors
- Bottom safe area positioning
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def format_srt_time(seconds: float) -> str:
    """Format seconds into SRT timestamp: HH:MM:SS,mmm"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msecs = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"


def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS timestamp: H:MM:SS.cc"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    csecs = int(round((seconds - int(seconds)) * 100))
    if csecs >= 100:
        csecs = 99
    return f"{hrs:d}:{mins:02d}:{secs:02d}.{csecs:02d}"


HIGHLIGHT_KEYWORDS = {
    "72", "double", "doubles", "doubling", "wealth", "freedom", "money", "compounding", "inflation",
    "percent", "math", "framing", "bias", "choices", "survival", "mortality", "decisions", "brain",
    "solid-state", "battery", "batteries", "energy", "ceramic", "fire", "aviation", "clean",
    "richat", "sahara", "eye", "magma", "asteroid", "crater", "wonders", "space", "station",
    "secret", "truth", "discover", "discovered", "hundred", "thousand", "million", "billion",
    "curiodaily", "follow", "tips", "daily"
}

# Pillar specific accent highlight colors in ASS format (&H00BBGGRR&)
PILLAR_HIGHLIGHT_COLORS = {
    "money_secrets": "&H0015CCFA&",     # Luminous Gold
    "human_psychology": "&H00FA8BA7&",  # Electric Lavender
    "future_is_here": "&H00EED322&",    # Neon Cyan
    "daily_mystery": "&H0024BFFB&",     # Luminous Amber
}


def highlight_chunk_text(chunk: str, highlight_color: str = "&H0015CCFA&") -> str:
    """Highlight numbers, percentages, and power keywords in punchy uppercase."""
    words = chunk.split()
    formatted = []
    for w in words:
        clean = re.sub(r"[^a-zA-Z0-9%]", "", w).lower()
        if any(c.isdigit() for c in clean) or clean in HIGHLIGHT_KEYWORDS or "%" in clean:
            formatted.append(f"{{\\c{highlight_color}}}{w.upper()}{{\\c&H00FFFFFF&}}")
        else:
            formatted.append(w.upper())
    return " ".join(formatted)


def create_srt_subtitles(scenes: List[Dict[str, Any]], output_path: Path) -> Path:
    """
    Generate standard .srt file with phrase-aligned captions from scenes.
    """
    srt_entries: List[str] = []
    index = 1

    for scene in scenes:
        narration = scene.get("narration", "").strip()
        start_t = float(scene.get("start_sec", 0.0))
        end_t = float(scene.get("end_sec", start_t + 4.0))
        duration = max(1.0, end_t - start_t)

        words = narration.split()
        if not words:
            continue

        chunk_size = 4
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        total_chars = max(1, sum(len(c) for c in chunks))

        curr_t = start_t
        for chunk in chunks:
            chunk_duration = duration * (len(chunk) / total_chars)
            c_start = curr_t
            c_end = c_start + chunk_duration
            curr_t = c_end

            srt_entries.append(
                f"{index}\n"
                f"{format_srt_time(c_start)} --> {format_srt_time(c_end)}\n"
                f"{chunk}\n"
            )
            index += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries))

    return output_path


def create_ass_subtitles(
    scenes: List[Dict[str, Any]],
    output_path: Path,
    category: str = "daily_mystery"
) -> Path:
    """
    Generate modern styled ASS subtitles:
    - Bold uppercase typography (Arial Black)
    - Translucent glassmorphism pill background box (BorderStyle=3)
    - Vibrant dynamic keyword and number highlights in pillar accent
    - Lower third safe area alignment (MarginV=110)
    """
    highlight_color = PILLAR_HIGHLIGHT_COLORS.get(category, "&H0015CCFA&")

    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ModernPill, Arial Black, 54, &H00FFFFFF, &H000000FF, &H80050B14, &HB00F172A, 1, 0, 0, 0, 100, 100, 2, 0, 3, 12, 0, 2, 60, 60, 250, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines: List[str] = []

    for scene in scenes:
        narration = scene.get("narration", "").strip()
        start_t = float(scene.get("start_sec", 0.0))
        end_t = float(scene.get("end_sec", start_t + 4.0))
        duration = max(1.0, end_t - start_t)

        words = narration.split()
        if not words:
            continue

        chunk_size = 4
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        total_chars = max(1, sum(len(c) for c in chunks))

        curr_t = start_t
        for chunk in chunks:
            chunk_duration = duration * (len(chunk) / total_chars)
            c_start = curr_t
            c_end = c_start + chunk_duration
            curr_t = c_end

            styled_text = highlight_chunk_text(chunk, highlight_color)
            t_start_str = format_ass_time(c_start)
            t_end_str = format_ass_time(c_end)

            dialogue_lines.append(
                f"Dialogue: 0,{t_start_str},{t_end_str},ModernPill,,0,0,0,,{styled_text}"
            )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(dialogue_lines) + "\n")

    return output_path
