"""
Visual assets generator using Pillow.
Creates high-contrast, branded 9:16 vertical frames for Reels,
and 4:5 vertical cards for Single-Image Feed Posts and Carousels.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from media.diagram_engine import draw_concept_diagram

logger = logging.getLogger(__name__)

# Color Palette Defaults (matching config/brand.yml)
PALETTES = {
    "money_secrets": {"primary": "#10B981", "accent": "#34D399", "badge": "MONEY SECRETS"},
    "human_psychology": {"primary": "#8B5CF6", "accent": "#A78BFA", "badge": "HUMAN MIND"},
    "future_is_here": {"primary": "#06B6D4", "accent": "#22D3EE", "badge": "FUTURE TECH"},
    "daily_mystery": {"primary": "#F59E0B", "accent": "#FBBF24", "badge": "DAILY MYSTERY"},
}
DEFAULT_BG = "#0F172A"       # Slate 900
DEFAULT_CARD_BG = "#1E293B"  # Slate 800
DEFAULT_TEXT = "#F8FAFC"     # Slate 50
DEFAULT_MUTED = "#94A3B8"    # Slate 400


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    hex_code = hex_code.lstrip("#")
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))  # type: ignore


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Load default truetype or standard fallback font."""
    font_names = ["arial.ttf", "arialbd.ttf" if bold else "arial.ttf", "DejaVuSans.ttf", "seguiemj.ttf"]
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def wrap_text(text: str, max_chars: int = 28) -> List[str]:
    words = text.split()
    lines = []
    current_line: List[str] = []
    current_len = 0

    for word in words:
        if current_len + len(word) + 1 <= max_chars:
            current_line.append(word)
            current_len += len(word) + 1
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_len = len(word)

    if current_line:
        lines.append(" ".join(current_line))
    return lines


def draw_outro_card(
    img: Image.Image,
    scene: Dict[str, Any],
    category: str,
    primary_color: Tuple[int, int, int],
    accent_color: Tuple[int, int, int],
    box: Tuple[int, int, int, int]
) -> None:
    """Render a premium branded outro call-to-action card."""
    draw = ImageDraw.Draw(img)
    card_left, card_top, card_right, card_bottom = box
    card_w = card_right - card_left
    card_h = card_bottom - card_top

    # Try loading CurioDaily logo icon
    logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo" / "logo_icon.png"
    logo_pasted = False
    if logo_path.exists():
        try:
            with Image.open(logo_path) as logo_img:
                logo_resized = logo_img.convert("RGBA").resize((200, 200), Image.Resampling.LANCZOS)
                lx = card_left + (card_w - 200) // 2
                ly = card_top + 70
                img.paste(logo_resized, (lx, ly), logo_resized)
                logo_pasted = True
        except Exception:
            logo_pasted = False

    if not logo_pasted:
        cx = card_left + card_w // 2
        cy = card_top + 170
        draw.ellipse([(cx - 90, cy - 90), (cx + 90, cy + 90)], outline=primary_color, width=10)
        draw.ellipse([(cx - 50, cy - 50), (cx + 50, cy + 50)], fill=primary_color)

    # Text: FOLLOW FOR DAILY TIPS
    cta_title_font = get_font(42, bold=True)
    draw.text((card_left + card_w // 2, card_top + 320), "FOLLOW FOR DAILY TIPS", fill=(255, 255, 255), font=cta_title_font, anchor="mm")

    # Handle: @CURIODAILY
    handle_font = get_font(54, bold=True)
    draw.text((card_left + card_w // 2, card_top + 390), "@CURIODAILY", fill=primary_color, font=handle_font, anchor="mm")

    # Subtitle
    sub_font = get_font(26, bold=False)
    draw.text((card_left + card_w // 2, card_top + 455), "Curiosity • Psychology • Money • Mysteries", fill=(148, 163, 184), font=sub_font, anchor="mm")

    # Divider line
    draw.line([(card_left + 80, card_top + 510), (card_right - 80, card_top + 510)], fill=(51, 65, 85), width=2)

    # Value props badge
    badge_font = get_font(26, bold=True)
    draw.text((card_left + card_w // 2, card_top + 560), "DON'T MISS OUT ON TOMORROW'S REEL", fill=accent_color, font=badge_font, anchor="mm")


def create_reel_scene_image(
    scene: Dict[str, Any],
    topic_title: str,
    category: str,
    output_path: Path,
    width: int = 1080,
    height: int = 1920
) -> Path:
    """
    Generate a 1080x1920 vertical image for a Reel scene.
    Includes category badge, prominent kinetic text, central illustration card,
    safe margins for Instagram Reels UI, and CurioDaily watermark.
    """
    palette = PALETTES.get(category, PALETTES["daily_mystery"])
    primary_color = hex_to_rgb(palette["primary"])
    bg_color = hex_to_rgb(DEFAULT_BG)
    card_bg = hex_to_rgb(DEFAULT_CARD_BG)
    text_color = hex_to_rgb(DEFAULT_TEXT)
    muted_color = hex_to_rgb(DEFAULT_MUTED)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 1. Subtle Background Accents / Grid Lines
    for y in range(200, height - 300, 250):
        draw.line([(60, y), (width - 60, y)], fill=(30, 41, 59), width=2)

    # 2. Top Safe Zone: CurioDaily Brand Watermark & Category Badge
    badge_text = palette["badge"]
    badge_font = get_font(32, bold=True)
    draw.rectangle([(80, 220), (80 + len(badge_text) * 22, 275)], fill=primary_color)
    draw.text((95, 228), badge_text, fill=(15, 23, 42), font=badge_font)

    watermark_font = get_font(28, bold=True)
    draw.text((width - 250, 232), "@CURIODAILY", fill=muted_color, font=watermark_font)

    # 3. Main Topic Title (Top area)
    title_font = get_font(52, bold=True)
    title_lines = wrap_text(topic_title, max_chars=24)
    y_text = 330
    for line in title_lines[:3]:
        draw.text((80, y_text), line, fill=text_color, font=title_font)
        y_text += 65

    # 4. Central Graphic Card (Safe center viewport: 580px to 1380px)
    card_top = 580
    card_bottom = 1380
    card_left = 70
    card_right = width - 70
    draw.rounded_rectangle([(card_left, card_top), (card_right, card_bottom)], radius=24, fill=card_bg, outline=primary_color, width=3)

    # Scene Header Tag within Card
    scene_section = scene.get("on_screen_text", "CONCEPT BREAKDOWN").upper()
    section_font = get_font(34, bold=True)
    draw.text((card_left + 40, card_top + 32), scene_section, fill=primary_color, font=section_font)

    # Check if this is the outro scene
    visual_type = scene.get("visual_type", "")
    section = scene.get("section", "")
    if visual_type == "outro" or section == "outro":
        card_box = (card_left, card_top, card_right, card_bottom)
        draw_outro_card(img, scene, category, primary_color, hex_to_rgb(palette.get("accent", palette["primary"])), card_box)
    else:
        # Check for external concept image (Wikimedia / NASA / local asset)
        image_path = scene.get("image_path")
        has_photo = False
        if image_path and Path(image_path).exists():
            try:
                with Image.open(image_path) as photo:
                    photo_rgb = photo.convert("RGB")
                    target_w = (card_right - card_left) - 40
                    target_h = (card_bottom - card_top) - 150
                    photo_rgb.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
                    px = card_left + 20 + (target_w - photo_rgb.width) // 2
                    py = card_top + 85 + (target_h - photo_rgb.height) // 2
                    img.paste(photo_rgb, (px, py))
                    has_photo = True
            except Exception as exc:
                logger.debug("Could not composite image %s: %s", image_path, exc)

        if not has_photo:
            # Render bespoke procedural concept diagram / infographic
            diagram_box = (card_left + 20, card_top + 75, card_right - 20, card_bottom - 75)
            draw_concept_diagram(img, scene, category, diagram_box, primary_color, hex_to_rgb(palette.get("accent", palette["primary"])))

        # Key insight footer pill within Card
        pill_text = scene.get("visual_description", "")
        if pill_text:
            pill_lines = wrap_text(pill_text, max_chars=36)
            if pill_lines:
                pill_font = get_font(24, bold=False)
                draw.text((card_left + 40, card_bottom - 50), pill_lines[0], fill=muted_color, font=pill_font)

    # 5. Scene Progress Indicator at Bottom Safe Margin (above 1600px UI safe boundary)
    scene_num = scene.get("scene_number", 1)
    total_scenes = 6
    progress_y = 1420
    bar_width = (width - 160) // total_scenes
    for s in range(total_scenes):
        bx = 80 + s * bar_width
        b_color = primary_color if s < scene_num else (51, 65, 85)
        draw.rounded_rectangle([(bx + 4, progress_y), (bx + bar_width - 8, progress_y + 12)], radius=6, fill=b_color)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "JPEG", quality=95)
    return output_path


def create_feed_post_image(
    post_data: Dict[str, Any],
    output_path: Path,
    width: int = 1080,
    height: int = 1350
) -> Path:
    """
    Generate a 1080x1350 (4:5) single-image feed post.
    """
    category = post_data.get("category", "daily_mystery")
    palette = PALETTES.get(category, PALETTES["daily_mystery"])
    primary_color = hex_to_rgb(palette["primary"])
    bg_color = hex_to_rgb(DEFAULT_BG)
    card_bg = hex_to_rgb(DEFAULT_CARD_BG)
    text_color = hex_to_rgb(DEFAULT_TEXT)
    muted_color = hex_to_rgb(DEFAULT_MUTED)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Top Brand Bar
    badge_font = get_font(28, bold=True)
    badge_text = palette["badge"]
    draw.rectangle([(70, 70), (70 + len(badge_text) * 20, 115)], fill=primary_color)
    draw.text((85, 78), badge_text, fill=(15, 23, 42), font=badge_font)

    draw.text((width - 240, 80), "@CURIODAILY", fill=muted_color, font=get_font(26, bold=True))

    # Headline
    headline = post_data.get("headline", post_data.get("title", ""))
    headline_font = get_font(56, bold=True)
    lines = wrap_text(headline, max_chars=22)
    y = 180
    for line in lines[:3]:
        draw.text((70, y), line, fill=text_color, font=headline_font)
        y += 72

    # Center Card
    card_top = 420
    card_bottom = 1100
    draw.rounded_rectangle([(70, card_top), (width - 70, card_bottom)], radius=24, fill=card_bg, outline=primary_color, width=3)

    image_path = post_data.get("image_path")
    has_photo = False
    if image_path and Path(image_path).exists():
        try:
            with Image.open(image_path) as photo:
                photo_rgb = photo.convert("RGB")
                target_w = (width - 140) - 30
                target_h = 360
                photo_rgb.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
                px = 70 + 15 + (target_w - photo_rgb.width) // 2
                py = card_top + 20
                img.paste(photo_rgb, (px, py))
                has_photo = True
        except Exception:
            has_photo = False

    label_font = get_font(30, bold=True)
    y_label = card_top + 400 if has_photo else card_top + 40
    draw.text((110, y_label), "THE SCIENTIFIC BREAKDOWN", fill=primary_color, font=label_font)

    body_text = post_data.get("core_insight", "")
    body_font = get_font(36 if has_photo else 40, bold=False)
    body_lines = wrap_text(body_text, max_chars=28)
    yb = y_label + 50
    max_body_lines = 4 if has_photo else 7
    for line in body_lines[:max_body_lines]:
        draw.text((110, yb), line, fill=text_color, font=body_font)
        yb += 48 if has_photo else 58

    # Fact Highlight
    fact_text = post_data.get("supporting_fact", "")
    if fact_text:
        fact_lines = wrap_text(f"Key Fact: {fact_text}", max_chars=32)
        y_fact = card_bottom - 50 if has_photo else 930
        draw.text((110, y_fact), fact_lines[0], fill=muted_color, font=get_font(26, bold=True))

    # Footer note
    draw.text((70, 1150), "Swipe or follow for daily evidence-based insights.", fill=muted_color, font=get_font(26, bold=False))
    draw.text((70, 1200), "CurioDaily • Verified Knowledge Engine", fill=muted_color, font=get_font(24, bold=True))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "JPEG", quality=95)
    return output_path


def create_carousel_slide_image(
    slide: Dict[str, Any],
    topic_title: str,
    category: str,
    slide_index: int,
    total_slides: int,
    output_path: Path,
    width: int = 1080,
    height: int = 1350
) -> Path:
    """
    Generate a 1080x1350 (4:5) carousel slide image.
    """
    palette = PALETTES.get(category, PALETTES["daily_mystery"])
    primary_color = hex_to_rgb(palette["primary"])
    bg_color = hex_to_rgb(DEFAULT_BG)
    card_bg = hex_to_rgb(DEFAULT_CARD_BG)
    text_color = hex_to_rgb(DEFAULT_TEXT)
    muted_color = hex_to_rgb(DEFAULT_MUTED)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Top Bar: Badge & Slide Index
    badge_text = palette["badge"]
    draw.rectangle([(70, 70), (70 + len(badge_text) * 20, 115)], fill=primary_color)
    draw.text((85, 78), badge_text, fill=(15, 23, 42), font=get_font(28, bold=True))

    counter_text = f"{slide_index:02d} / {total_slides:02d}"
    draw.text((width - 180, 78), counter_text, fill=primary_color, font=get_font(32, bold=True))

    # Main Section
    slide_type = slide.get("type", "insight")
    slide_title = slide.get("title", "")
    slide_text = slide.get("text", slide.get("subtitle", ""))

    if slide_type == "cover":
        # Cover slide layout
        image_path = slide.get("image_path")
        has_photo = False
        if image_path and Path(image_path).exists():
            try:
                with Image.open(image_path) as photo:
                    photo_rgb = photo.convert("RGB")
                    target_w = width - 140
                    target_h = 360
                    photo_rgb.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
                    px = 70 + (target_w - photo_rgb.width) // 2
                    py = 180
                    img.paste(photo_rgb, (px, py))
                    has_photo = True
            except Exception:
                has_photo = False

        title_lines = wrap_text(topic_title, max_chars=18)
        y = 570 if has_photo else 350
        title_font = get_font(56 if has_photo else 68, bold=True)
        for line in title_lines[:3 if has_photo else 4]:
            draw.text((70, y), line, fill=text_color, font=title_font)
            y += 72 if has_photo else 85

        draw.rounded_rectangle([(70, y + 40), (width - 70, y + 200)], radius=20, fill=card_bg, outline=primary_color, width=2)
        sub_lines = wrap_text(slide_text, max_chars=28)
        ys = y + 70
        for line in sub_lines[:2]:
            draw.text((110, ys), line, fill=primary_color, font=get_font(34, bold=True))
            ys += 50

        draw.text((70, 1200), "SWIPE FOR BREAKDOWN ➔", fill=text_color, font=get_font(34, bold=True))

    else:
        # Content slide layout
        title_font = get_font(52, bold=True)
        draw.text((70, 200), slide_title, fill=primary_color, font=title_font)

        # Topic Reference Header
        draw.text((70, 280), topic_title[:45], fill=muted_color, font=get_font(30, bold=False))

        # Main Card
        draw.rounded_rectangle([(70, 360), (width - 70, 1050)], radius=24, fill=card_bg, outline=primary_color, width=3)
        body_font = get_font(42, bold=False)
        text_lines = wrap_text(slide_text, max_chars=25)
        yt = 450
        for line in text_lines[:8]:
            draw.text((120, yt), line, fill=text_color, font=body_font)
            yt += 65

        # Footer CTA or Swipe hint
        footer_text = "CurioDaily • Verified Research" if slide_index == total_slides else "SWIPE NEXT ➔"
        draw.text((70, 1200), footer_text, fill=muted_color, font=get_font(28, bold=True))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "JPEG", quality=95)
    return output_path
