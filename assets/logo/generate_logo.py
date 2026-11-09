"""
Generate branded CurioDaily logo and watermark PNG assets with transparency.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def generate_curiodaily_logos(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Square Brand Icon (512x512)
    icon = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)

    # Rounded background
    draw.rounded_rectangle([(16, 16), (496, 496)], radius=120, fill=(15, 23, 42, 255))
    # Border
    draw.rounded_rectangle([(16, 16), (496, 496)], radius=120, outline=(56, 189, 248, 255), width=8)

    # Glowing ring
    draw.ellipse([(120, 120), (392, 392)], outline=(56, 189, 248, 255), width=18)
    draw.ellipse([(190, 190), (322, 322)], fill=(16, 185, 129, 255))

    icon_path = output_dir / "logo_icon.png"
    icon.save(str(icon_path), "PNG")

    # 2. Horizontal Watermark (600x120)
    watermark = Image.new("RGBA", (600, 120), (0, 0, 0, 0))
    wdraw = ImageDraw.Draw(watermark)

    try:
        font = ImageFont.truetype("arialbd.ttf", 52)
    except Exception:
        font = ImageFont.load_default()

    wdraw.text((30, 28), "CURIODAILY", fill=(248, 250, 252, 220), font=font)
    wdraw.ellipse([(380, 48), (405, 73)], fill=(56, 189, 248, 240))

    watermark_path = output_dir / "watermark.png"
    watermark.save(str(watermark_path), "PNG")
    print(f"Generated logo icon at {icon_path} and watermark at {watermark_path}")


if __name__ == "__main__":
    generate_curiodaily_logos(Path(__file__).resolve().parent)
