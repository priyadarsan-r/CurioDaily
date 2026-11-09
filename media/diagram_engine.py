"""
Procedural diagram and scientific infographic generator using Pillow.
Creates high-contrast, topic-aligned visual charts, curves, and schematics
specifically engineered for 1080x1920 vertical mobile viewports.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple
from PIL import Image, ImageDraw, ImageFont


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    hex_code = hex_code.lstrip("#")
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))  # type: ignore


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    font_names = ["arial.ttf", "arialbd.ttf" if bold else "arial.ttf", "DejaVuSans.ttf", "seguiemj.ttf"]
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_exponential_growth(
    draw: ImageDraw.ImageDraw,
    box: Tuple[int, int, int, int],
    primary_color: Tuple[int, int, int],
    accent_color: Tuple[int, int, int]
) -> None:
    """Draw compound interest hockey-stick exponential curve."""
    left, top, right, bottom = box
    w = right - left
    h = bottom - top

    # Axes
    axis_x = left + 70
    axis_y = bottom - 70
    draw.line([(axis_x, top + 40), (axis_x, axis_y)], fill=(100, 116, 139), width=3)
    draw.line([(axis_x, axis_y), (right - 40, axis_y)], fill=(100, 116, 139), width=3)

    # Grid marks
    font_sm = get_font(22, bold=True)
    draw.text((axis_x - 50, top + 35), "$$$", fill=(148, 163, 184), font=font_sm)
    draw.text((right - 100, axis_y + 15), "TIME ➔", fill=(148, 163, 184), font=font_sm)

    # Linear comparison line (Simple Saving)
    draw.line([(axis_x, axis_y), (right - 60, axis_y - int(h * 0.35))], fill=(71, 85, 105), width=3)
    draw.text((right - 280, axis_y - int(h * 0.33)), "Linear Savings", fill=(100, 116, 139), font=get_font(20, bold=False))

    # Exponential Curve points
    curve_points: List[Tuple[float, float]] = []
    num_steps = 40
    curve_w = (right - 60) - axis_x
    curve_h = axis_y - (top + 60)
    for i in range(num_steps + 1):
        t = i / num_steps
        px = axis_x + t * curve_w
        py = axis_y - (math.exp(t * 2.8) - 1) / (math.exp(2.8) - 1) * curve_h
        curve_points.append((px, py))

    # Draw glow & curve
    for i in range(len(curve_points) - 1):
        draw.line([curve_points[i], curve_points[i+1]], fill=primary_color, width=6)

    # Highlight Inflection Point & Final Point
    inflection_idx = int(num_steps * 0.65)
    ix, iy = curve_points[inflection_idx]
    draw.ellipse([(ix - 8, iy - 8), (ix + 8, iy + 8)], fill=accent_color, outline=(255, 255, 255), width=2)
    draw.text((ix - 160, iy - 45), "Inflection Point", fill=accent_color, font=get_font(24, bold=True))

    fx, fy = curve_points[-1]
    draw.ellipse([(fx - 10, fy - 10), (fx + 10, fy + 10)], fill=(255, 255, 255), outline=primary_color, width=3)
    draw.text((fx - 240, fy - 15), "10X COMPOUND", fill=(255, 255, 255), font=get_font(26, bold=True))


def draw_dunning_kruger_curve(
    draw: ImageDraw.ImageDraw,
    box: Tuple[int, int, int, int],
    primary_color: Tuple[int, int, int],
    accent_color: Tuple[int, int, int]
) -> None:
    """Draw Dunning-Kruger cognitive confidence vs competence curve."""
    left, top, right, bottom = box
    w = right - left
    h = bottom - top

    axis_x = left + 60
    axis_y = bottom - 70
    draw.line([(axis_x, top + 40), (axis_x, axis_y)], fill=(100, 116, 139), width=3)
    draw.line([(axis_x, axis_y), (right - 40, axis_y)], fill=(100, 116, 139), width=3)

    font_sm = get_font(22, bold=True)
    draw.text((axis_x - 45, top + 15), "CONFIDENCE", fill=(148, 163, 184), font=font_sm)
    draw.text((right - 180, axis_y + 15), "EXPERIENCE ➔", fill=(148, 163, 184), font=font_sm)

    # Dunning-Kruger shape: sharp peak early, steep drop to valley, gradual rise
    cw = (right - 60) - axis_x
    ch = axis_y - (top + 70)

    p0 = (axis_x, axis_y)
    p_peak = (axis_x + cw * 0.22, top + 75)
    p_valley = (axis_x + cw * 0.50, axis_y - ch * 0.15)
    p_slope = (axis_x + cw * 0.75, axis_y - ch * 0.50)
    p_mastery = (axis_x + cw * 0.98, axis_y - ch * 0.75)

    # Interpolate smooth curve
    points = [p0]
    for step in range(1, 15):
        t = step / 15
        points.append((p0[0] + (p_peak[0] - p0[0]) * t, p0[1] + (p_peak[1] - p0[1]) * (t**0.6)))
    for step in range(1, 20):
        t = step / 20
        points.append((p_peak[0] + (p_valley[0] - p_peak[0]) * t, p_peak[1] + (p_valley[1] - p_peak[1]) * (t**1.8)))
    for step in range(1, 25):
        t = step / 25
        points.append((p_valley[0] + (p_mastery[0] - p_valley[0]) * t, p_valley[1] + (p_mastery[1] - p_valley[1]) * (t**0.8)))

    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=primary_color, width=6)

    # Labels on key psychological landmarks
    draw.ellipse([(p_peak[0]-8, p_peak[1]-8), (p_peak[0]+8, p_peak[1]+8)], fill=(239, 68, 68))
    draw.text((p_peak[0] - 80, p_peak[1] - 45), "Peak of 'Know-it-All'", fill=(248, 113, 113), font=get_font(22, bold=True))

    draw.ellipse([(p_valley[0]-8, p_valley[1]-8), (p_valley[0]+8, p_valley[1]+8)], fill=(245, 158, 11))
    draw.text((p_valley[0] - 60, p_valley[1] + 15), "Valley of Despair", fill=(251, 191, 36), font=get_font(22, bold=True))

    draw.ellipse([(p_mastery[0]-8, p_mastery[1]-8), (p_mastery[0]+8, p_mastery[1]+8)], fill=(52, 211, 153))
    draw.text((p_mastery[0] - 160, p_mastery[1] - 40), "Plateau of Mastery", fill=(52, 211, 153), font=get_font(22, bold=True))


def draw_energy_density_chart(
    draw: ImageDraw.ImageDraw,
    box: Tuple[int, int, int, int],
    primary_color: Tuple[int, int, int],
    accent_color: Tuple[int, int, int]
) -> None:
    """Draw battery energy density comparison bar chart (Wh/kg)."""
    left, top, right, bottom = box
    w = right - left
    bar_left = left + 60
    max_bar_w = w - 240

    bars = [
        {"name": "Solid-State Battery", "value": 450, "unit": "450 Wh/kg", "color": primary_color, "highlight": True},
        {"name": "Conventional Li-ion", "value": 260, "unit": "260 Wh/kg", "color": (100, 116, 139), "highlight": False},
        {"name": "Lead-Acid", "value": 45, "unit": "45 Wh/kg", "color": (51, 65, 85), "highlight": False},
    ]

    y_cursor = top + 60
    for bar in bars:
        ratio = bar["value"] / 500.0
        cur_w = int(max_bar_w * ratio)

        # Label
        label_font = get_font(26, bold=bar["highlight"])
        label_col = (255, 255, 255) if bar["highlight"] else (148, 163, 184)
        draw.text((bar_left, y_cursor), bar["name"], fill=label_col, font=label_font)

        # Bar rect
        by = y_cursor + 38
        draw.rounded_rectangle([(bar_left, by), (bar_left + cur_w, by + 34)], radius=8, fill=bar["color"])
        # Unit text
        draw.text((bar_left + cur_w + 18, by + 4), bar["unit"], fill=label_col, font=get_font(24, bold=True))

        if bar["highlight"]:
            badge_x = bar_left + cur_w - 110
            draw.text((badge_x, by + 6), "+73% GAIN", fill=(15, 23, 42), font=get_font(20, bold=True))

        y_cursor += 120

    # Key callout box
    callout_top = y_cursor + 20
    draw.rounded_rectangle([(bar_left, callout_top), (right - 60, callout_top + 100)], radius=12, fill=(30, 41, 59), outline=primary_color, width=2)
    draw.text((bar_left + 25, callout_top + 18), "KEY BREAKTHROUGH: ZERO FIRE RISK", fill=primary_color, font=get_font(22, bold=True))
    draw.text((bar_left + 25, callout_top + 52), "Non-flammable ceramic electrolyte replaces liquid solvent.", fill=(203, 213, 225), font=get_font(20, bold=False))


def draw_wow_signal_spectrogram(
    draw: ImageDraw.ImageDraw,
    box: Tuple[int, int, int, int],
    primary_color: Tuple[int, int, int],
    accent_color: Tuple[int, int, int]
) -> None:
    """Draw the famous 1977 Wow! Signal radio frequency transmission wave."""
    left, top, right, bottom = box
    w = right - left
    h = bottom - top

    axis_x = left + 60
    axis_y = bottom - 70
    draw.line([(axis_x, top + 40), (axis_x, axis_y)], fill=(100, 116, 139), width=2)
    draw.line([(axis_x, axis_y), (right - 40, axis_y)], fill=(100, 116, 139), width=2)

    font_sm = get_font(20, bold=True)
    draw.text((axis_x - 40, top + 15), "SIGNAL INTENSITY (SNR)", fill=(148, 163, 184), font=font_sm)
    draw.text((right - 220, axis_y + 15), "72-SEC TRANSIT ➔", fill=(148, 163, 184), font=font_sm)

    # Bell curve of transit intensity
    steps = 40
    cw = (right - 60) - axis_x
    ch = axis_y - (top + 90)
    wave_pts: List[Tuple[float, float]] = []
    for i in range(steps + 1):
        x_norm = (i - steps / 2) / 6.0
        y_val = math.exp(-0.5 * (x_norm ** 2))
        px = axis_x + (i / steps) * cw
        py = axis_y - y_val * ch
        wave_pts.append((px, py))

    # Fill background beneath peak
    for i in range(len(wave_pts) - 1):
        draw.line([wave_pts[i], wave_pts[i+1]], fill=primary_color, width=5)

    # Highlight Peak: '6EQUJ5'
    peak_pt = wave_pts[steps // 2]
    draw.ellipse([(peak_pt[0]-12, peak_pt[1]-12), (peak_pt[0]+12, peak_pt[1]+12)], fill=(239, 68, 68), outline=(255, 255, 255), width=3)
    draw.text((peak_pt[0] - 70, peak_pt[1] - 50), "CODE: 6EQUJ5", fill=(248, 113, 113), font=get_font(28, bold=True))

    # Annotation badge
    draw.rounded_rectangle([(left + 80, bottom - 180), (right - 80, bottom - 90)], radius=12, fill=(30, 41, 59), outline=(239, 68, 68), width=2)
    draw.text((left + 105, bottom - 165), "1420.455 MHz • 30X COSMIC BACKGROUND", fill=(255, 255, 255), font=get_font(22, bold=True))
    draw.text((left + 105, bottom - 130), "Hydrogen line signal recorded at Big Ear Observatory.", fill=(203, 213, 225), font=get_font(19, bold=False))


def draw_concept_diagram(
    img: Image.Image,
    scene: Dict[str, Any],
    category: str,
    box: Tuple[int, int, int, int],
    primary_color: Tuple[int, int, int],
    accent_color: Tuple[int, int, int]
) -> None:
    """
    Select and render the appropriate concept illustration or diagram
    based on pillar, scene type, and script content.
    """
    draw = ImageDraw.Draw(img)
    scene_num = scene.get("scene_number", 1)
    visual_type = scene.get("visual_type", "")
    narration = scene.get("narration", "").lower()

    if category == "money_secrets":
        if scene_num in (2, 3) or "compound" in narration or "interest" in narration or "growth" in narration or "data_chart" in visual_type:
            draw_exponential_growth(draw, box, primary_color, accent_color)
        else:
            draw_exponential_growth(draw, box, primary_color, accent_color)

    elif category == "human_psychology":
        if scene_num in (2, 3, 4) or "dunning" in narration or "confidence" in narration or "bias" in narration:
            draw_dunning_kruger_curve(draw, box, primary_color, accent_color)
        else:
            draw_dunning_kruger_curve(draw, box, primary_color, accent_color)

    elif category == "future_is_here":
        if scene_num in (2, 3, 4) or "battery" in narration or "energy" in narration or "density" in narration:
            draw_energy_density_chart(draw, box, primary_color, accent_color)
        else:
            draw_energy_density_chart(draw, box, primary_color, accent_color)

    elif category == "daily_mystery":
        if scene_num in (2, 3, 4) or "signal" in narration or "radio" in narration or "space" in narration or "wow" in narration:
            draw_wow_signal_spectrogram(draw, box, primary_color, accent_color)
        else:
            draw_wow_signal_spectrogram(draw, box, primary_color, accent_color)

    else:
        # Fallback default curve
        draw_exponential_growth(draw, box, primary_color, accent_color)
