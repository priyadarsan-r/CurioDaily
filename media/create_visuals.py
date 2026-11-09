"""
Visual assets generator using Pillow.
Creates high-contrast, branded 9:16 vertical frames for Reels,
and 4:5 vertical cards for Single-Image Feed Posts and Carousels.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
    """Render a clean cinematic conclusion card with zero branding."""
    draw = ImageDraw.Draw(img)
    card_left, card_top, card_right, card_bottom = box
    card_w = card_right - card_left
    card_h = card_bottom - card_top

    cx = card_left + card_w // 2
    cy = card_top + 160
    draw.ellipse([(cx - 70, cy - 70), (cx + 70, cy + 70)], outline=primary_color, width=6)
    draw.ellipse([(cx - 40, cy - 40), (cx + 40, cy + 40)], fill=accent_color)

    title_font = get_font(42, bold=True)
    draw.text((cx, card_top + 280), "KEY TAKEAWAY", fill=(255, 255, 255), font=title_font, anchor="mm")

    text = scene.get("narration", scene.get("visual_description", ""))
    lines = wrap_text(text, max_chars=28)
    body_font = get_font(32, bold=False)
    y_pos = card_top + 360
    for line in lines[:4]:
        draw.text((cx, y_pos), line, fill=(241, 245, 249), font=body_font, anchor="mm")
        y_pos += 50


def compose_movie_subjects(
    img: Image.Image,
    prompt: str,
    category: str,
    scene_num: int = 1,
    width: int = 1080,
    height: int = 1920
) -> Image.Image:
    """
    Renders tangible real-world short-movie subjects (people arguing, walking,
    skits, physical cash stacks, gold vaults, vehicles, cityscapes, technology).
    """
    p = prompt.lower()
    subject_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(subject_layer)

    # 1. Action: 2 People in Skit / Argument / Dialogue
    if any(k in p for k in ["two", "arguing", "debate", "skit", "colleague", "partner", "people", "doctor", "patient", "friends"]):
        # Interior boardroom / office setting
        draw.rectangle([(120, 350), (960, 1100)], fill=(15, 23, 42, 60), outline=(51, 65, 85, 120), width=4)
        for wx in range(200, 900, 140):
            draw.line([(wx, 350), (wx, 1100)], fill=(30, 41, 59, 100), width=2)
            
        # Foreground conference table / desk
        table_top = 1180
        draw.rectangle([(80, table_top), (width - 80, 1340)], fill=(12, 16, 24, 250))
        
        # Physical cash stacks or contracts on table
        for ox in [300, 370, 440, 510, 580, 650]:
            draw.rectangle([(ox, table_top - 50), (ox + 55, table_top)], fill=(22, 36, 30, 240), outline=(52, 211, 153, 200), width=2)

        # Character 1 (Left): Leaning forward arguing / gesturing
        draw.ellipse([(190, 830), (330, 970)], fill=(8, 12, 18, 255))
        draw.polygon([(140, table_top), (250, 970), (360, 990), (450, table_top)], fill=(8, 12, 18, 255))
        draw.polygon([(340, 1020), (520, 1100), (500, 1130), (320, 1060)], fill=(8, 12, 18, 255))

        # Character 2 (Right): Sitting upright listening / reacting
        draw.ellipse([(750, 840), (890, 980)], fill=(8, 12, 18, 255))
        draw.polygon([(640, table_top), (750, 980), (870, 980), (940, table_top)], fill=(8, 12, 18, 255))
        draw.polygon([(750, 1040), (650, 1120), (670, 1140), (780, 1060)], fill=(8, 12, 18, 255))

    # 2. Action: 2 People Walking side-by-side down street / avenue
    elif any(k in p for k in ["walking", "street", "avenue", "couple", "path", "outdoor"]):
        # Distant skyscrapers
        draw.polygon([(100, 1200), (100, 550), (280, 550), (280, 1200)], fill=(15, 23, 42, 140))
        draw.polygon([(320, 1200), (320, 420), (540, 420), (540, 1200)], fill=(12, 18, 30, 160))
        draw.polygon([(600, 1200), (600, 500), (800, 500), (800, 1200)], fill=(15, 23, 42, 140))
        
        # Ground street perspective
        draw.polygon([(0, 1400), (width, 1400), (width, height), (0, height)], fill=(10, 15, 22, 255))
        
        # Character 1 walking (left)
        draw.ellipse([(320, 880), (420, 980)], fill=(6, 10, 16, 255))
        draw.polygon([(290, 1400), (350, 980), (430, 980), (460, 1400)], fill=(6, 10, 16, 255))
        draw.polygon([(410, 1060), (480, 1080), (470, 1110), (400, 1090)], fill=(6, 10, 16, 255))

        # Character 2 walking (right)
        draw.ellipse([(580, 900), (680, 1000)], fill=(6, 10, 16, 255))
        draw.polygon([(550, 1400), (610, 1000), (690, 1000), (720, 1400)], fill=(6, 10, 16, 255))

    # 3. Money & Wealth: Bank Vault / Gold Bullion / Cash Stacks
    elif any(k in p for k in ["vault", "gold", "bullion", "cash", "bank", "currency", "treasury"]):
        cx, cy = width // 2, 850
        draw.ellipse([(cx - 320, cy - 320), (cx + 320, cy + 320)], fill=(15, 23, 42, 240), outline=(245, 158, 11, 200), width=12)
        draw.ellipse([(cx - 240, cy - 240), (cx + 240, cy + 240)], fill=(10, 16, 26, 240), outline=(245, 158, 11, 140), width=6)
        draw.ellipse([(cx - 80, cy - 80), (cx + 80, cy + 80)], fill=(245, 158, 11, 160))
        for deg in [0, 45, 90, 135, 180, 225, 270, 315]:
            rad = np.radians(deg)
            x1 = cx + int(100 * np.cos(rad))
            y1 = cy + int(100 * np.sin(rad))
            x2 = cx + int(230 * np.cos(rad))
            y2 = cy + int(230 * np.sin(rad))
            draw.line([(x1, y1), (x2, y2)], fill=(245, 158, 11, 220), width=8)

        # Stacks of gold bars in foreground
        for gy, count in [(1250, 5), (1200, 4), (1150, 3)]:
            for i in range(count):
                bx = 320 + (5 - count) * 45 + i * 90
                draw.polygon([(bx, gy), (bx + 80, gy), (bx + 95, gy - 35), (bx + 15, gy - 35)], fill=(217, 119, 6, 255), outline=(251, 191, 36, 255), width=2)

    # 4. Technology, Aircraft, Vehicle or Science Laboratory
    elif any(k in p for k in ["vehicle", "aircraft", "car", "cleanroom", "laboratory", "robot", "satellite", "battery", "technology"]):
        draw.polygon([(100, 1300), (width - 100, 1300), (width, height), (0, height)], fill=(8, 14, 24, 255))
        cx, cy = width // 2, 750
        draw.ellipse([(cx - 260, cy - 260), (cx + 260, cy + 260)], outline=(6, 182, 212, 180), width=6)
        draw.ellipse([(cx - 180, cy - 180), (cx + 180, cy + 180)], outline=(34, 211, 238, 220), width=3)
        draw.ellipse([(cx - 60, cy + 220), (cx + 60, cy + 340)], fill=(6, 12, 20, 255))
        draw.polygon([(cx - 140, 1300), (cx - 70, cy + 340), (cx + 70, cy + 340), (cx + 140, 1300)], fill=(6, 12, 20, 255))

    # 5. Mystery / Nature / Astronomy / Desert Expedition
    else:
        draw.polygon([(0, 1100), (350, 950), (750, 1080), (width, 920), (width, height), (0, height)], fill=(14, 18, 26, 255))
        cx, cy = 420, 920
        draw.polygon([(cx, cy - 300), (cx + 120, cy - 280), (cx + 100, cy + 60), (cx - 20, cy + 60)], fill=(8, 12, 18, 255), outline=(245, 158, 11, 100), width=3)
        draw.ellipse([(620, 950), (690, 1020)], fill=(6, 10, 16, 255))
        draw.polygon([(590, 1150), (630, 1020), (680, 1020), (710, 1150)], fill=(6, 10, 16, 255))
        draw.line([(680, 1050), (740, 990)], fill=(6, 10, 16, 255), width=8)
        draw.ellipse([(760, 960), (830, 1030)], fill=(6, 10, 16, 255))
        draw.polygon([(730, 1150), (770, 1030), (820, 1030), (850, 1150)], fill=(6, 10, 16, 255))

    return Image.alpha_composite(img.convert("RGBA"), subject_layer).convert("RGB")


def create_reel_scene_image(
    scene: Dict[str, Any],
    topic_title: str,
    category: str,
    output_path: Path,
    width: int = 1080,
    height: int = 1920
) -> Path:
    """
    Generate a 1080x1920 full-bleed vertical cinematic frame for a Reel scene.
    Professional cinema look: ZERO top headings, ZERO scene numbers, ZERO cards,
    and ZERO 2D diagram/chart lines. Only pure real-world photography and lighting.
    """
    # 1. If an actual photo / image path exists, aspect-fill crop to full 1080x1920
    image_path = scene.get("image_path")
    if image_path and Path(image_path).exists():
        try:
            with Image.open(image_path) as photo:
                photo_rgb = photo.convert("RGB")
                ratio = max(width / photo_rgb.width, height / photo_rgb.height)
                new_size = (int(photo_rgb.width * ratio), int(photo_rgb.height * ratio))
                resized = photo_rgb.resize(new_size, Image.Resampling.LANCZOS)
                left = (resized.width - width) // 2
                top = (resized.height - height) // 2
                cropped = resized.crop((left, top, left + width, top + height))

                output_path.parent.mkdir(parents=True, exist_ok=True)
                cropped.save(str(output_path), "JPEG", quality=95)
                return output_path
        except Exception as exc:
            logger.debug("Failed opening image_path %s: %s", image_path, exc)

    # 2. Procedural Real-World Cinematic Frame Synthesis
    color_presets = {
        "money_secrets": ((10, 22, 28), (16, 185, 129)),       # Deep noir to emerald glow
        "human_psychology": ((18, 12, 32), (139, 92, 246)),    # Deep obsidian to amethyst violet
        "future_is_here": ((8, 20, 32), (6, 182, 212)),        # Deep space cyan to electric teal
        "daily_mystery": ((28, 16, 10), (245, 158, 11)),       # Warm ember to golden amber
    }
    base_dark, accent_light = color_presets.get(category, color_presets["daily_mystery"])

    y = np.linspace(0, 1, height)[:, None]
    x = np.linspace(0, 1, width)[None, :]

    scene_num = scene.get("scene_number", 1)
    cx = 0.35 + 0.3 * ((scene_num * 3) % 5) / 5.0
    cy = 0.3 + 0.2 * ((scene_num * 2) % 4) / 4.0
    dist = np.sqrt((x - cx) ** 2 * 1.6 + (y - cy) ** 2)
    key_light = np.exp(-dist * 2.2)

    bottom_fill = np.exp(-((1.0 - y) ** 2) * 2.0) * 0.25

    r = (base_dark[0] + key_light * (accent_light[0] - base_dark[0]) * 0.75 + bottom_fill * 20).clip(0, 255)
    g = (base_dark[1] + key_light * (accent_light[1] - base_dark[1]) * 0.75 + bottom_fill * 20).clip(0, 255)
    b = (base_dark[2] + key_light * (accent_light[2] - base_dark[2]) * 0.75 + bottom_fill * 20).clip(0, 255)

    grain = np.random.normal(0, 5.5, (height, width))
    r = np.clip(r + grain, 0, 255).astype(np.uint8)
    g = np.clip(g + grain, 0, 255).astype(np.uint8)
    b = np.clip(b + grain, 0, 255).astype(np.uint8)

    rgb = np.stack([r, g, b], axis=-1)
    img = Image.fromarray(rgb)

    # Anamorphic horizontal lens flare glow
    flare = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    fdraw = ImageDraw.Draw(flare)
    flare_y = int(cy * height)
    flare_color = (accent_light[0], accent_light[1], accent_light[2], 45)
    fdraw.ellipse([(-100, flare_y - 25), (width + 100, flare_y + 25)], fill=flare_color)
    flare = flare.filter(ImageFilter.GaussianBlur(35))
    img = Image.alpha_composite(img.convert("RGBA"), flare).convert("RGB")

    # Composite tangible short movie subjects (people arguing, walking, vaults, cash, tech)
    prompt_desc = scene.get("imagen_prompt", scene.get("visual_description", topic_title))
    img = compose_movie_subjects(img, prompt_desc, category, scene_num=scene_num, width=width, height=height)

    # Cinematic perimeter vignette (dark corners for film lens realism)
    vignette = Image.new("L", (width, height), 255)
    vdraw = ImageDraw.Draw(vignette)
    vdraw.ellipse([(-180, -180), (width + 180, height + 180)], fill=0)
    vignette = vignette.filter(ImageFilter.GaussianBlur(150))
    img.paste((0, 0, 0), mask=vignette)

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

    # Headline (Clean top layout without brand watermarks)
    headline = post_data.get("headline", post_data.get("title", ""))
    headline_font = get_font(56, bold=True)
    lines = wrap_text(headline, max_chars=22)
    y = 100
    for line in lines[:3]:
        draw.text((70, y), line, fill=text_color, font=headline_font)
        y += 72

    # Center Card
    card_top = 360
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

    # Footer note (Unbranded)
    draw.text((70, 1160), "Documented by verified peer-reviewed scientific research.", fill=muted_color, font=get_font(26, bold=False))

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
    Generate a 1080x1350 (4:5) carousel slide image without branding.
    """
    palette = PALETTES.get(category, PALETTES["daily_mystery"])
    primary_color = hex_to_rgb(palette["primary"])
    bg_color = hex_to_rgb(DEFAULT_BG)
    card_bg = hex_to_rgb(DEFAULT_CARD_BG)
    text_color = hex_to_rgb(DEFAULT_TEXT)
    muted_color = hex_to_rgb(DEFAULT_MUTED)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Top Bar: Slide Index
    counter_text = f"{slide_index:02d} / {total_slides:02d}"
    draw.text((width - 180, 70), counter_text, fill=primary_color, font=get_font(32, bold=True))

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

        # Footer Takeaway or Swipe hint
        footer_text = "Summary & Strategic Takeaway" if slide_index == total_slides else "SWIPE NEXT ➔"
        draw.text((70, 1200), footer_text, fill=muted_color, font=get_font(28, bold=True))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "JPEG", quality=95)
    return output_path
