from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "test-zone-screenshot.png"


def create_test_zone_image(output_path: Path = DEFAULT_OUTPUT) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (900, 900), (45, 83, 58))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=22)
    small_font = ImageFont.load_default(size=16)

    _draw_map_background(draw)
    _draw_compounds(draw)
    _draw_zone_circles(draw)
    _draw_labels(draw, font, small_font)

    image.save(output_path, format="PNG", optimize=True)
    return output_path


def _draw_map_background(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((0, 0, 900, 105), fill=(42, 95, 118))
    draw.rectangle((0, 780, 900, 900), fill=(42, 95, 118))
    draw.polygon(
        [
            (70, 780),
            (150, 250),
            (300, 150),
            (470, 665),
            (560, 130),
            (820, 210),
            (760, 820),
        ],
        fill=(58, 103, 70),
    )

    draw.line((70, 720, 820, 160), fill=(174, 161, 132), width=10)
    draw.line((120, 255, 780, 660), fill=(174, 161, 132), width=8)
    draw.line((105, 535, 505, 310), fill=(126, 119, 102), width=5)

    for x in range(0, 901, 150):
        draw.line((x, 0, x, 900), fill=(72, 96, 86), width=1)
    for y in range(0, 901, 150):
        draw.line((0, y, 900, y), fill=(72, 96, 86), width=1)


def _draw_compounds(draw: ImageDraw.ImageDraw) -> None:
    compounds = [
        (245, 330, "School"),
        (305, 350, "Apartments"),
        (360, 315, "Hill"),
        (615, 500, "Farm"),
        (670, 535, "Compound"),
        (700, 485, "Roadside"),
    ]
    for x, y, _ in compounds:
        draw.rectangle((x, y, x + 42, y + 28), fill=(103, 95, 76), outline=(198, 187, 143), width=2)
        draw.rectangle((x + 8, y + 34, x + 28, y + 48), fill=(90, 84, 68), outline=(170, 157, 120))


def _draw_zone_circles(draw: ImageDraw.ImageDraw) -> None:
    draw.ellipse((80, 160, 820, 800), outline=(74, 180, 255), width=8)
    draw.ellipse((280, 235, 720, 675), outline=(255, 255, 255), width=8)
    draw.ellipse((410, 285, 710, 585), outline=(255, 255, 255), width=7)
    draw.ellipse((525 - 8, 442 - 8, 525 + 8, 442 + 8), fill=(255, 220, 75), outline=(30, 30, 30), width=2)


def _draw_labels(draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont, small_font: ImageFont.ImageFont) -> None:
    draw.rectangle((18, 18, 320, 70), fill=(18, 23, 30), outline=(240, 240, 240))
    draw.text((32, 32), "ERANGEL | PHASE 5 TEST", fill=(255, 255, 255), font=font)
    draw.text((432, 18), "N", fill=(255, 255, 255), font=font)
    draw.text((432, 862), "S", fill=(255, 255, 255), font=font)
    draw.text((18, 438), "W", fill=(255, 255, 255), font=font)
    draw.text((862, 438), "E", fill=(255, 255, 255), font=font)

    labels = [
        (245, 302, "School"),
        (305, 404, "Apts"),
        (615, 472, "Farm"),
        (665, 588, "Compound"),
    ]
    for x, y, label in labels:
        draw.rounded_rectangle((x - 6, y - 4, x + 88, y + 21), radius=5, fill=(20, 26, 34))
        draw.text((x, y), label, fill=(238, 242, 245), font=small_font)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a synthetic PUBG zone screenshot for local testing.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output PNG path. Default: {DEFAULT_OUTPUT}",
    )
    args = parser.parse_args()

    output_path = create_test_zone_image(args.output)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
