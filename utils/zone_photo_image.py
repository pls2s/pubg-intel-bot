from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from models.zone import ZoneImagePrediction


MAX_OUTPUT_SIZE = 1600
SAFE_COLOR = (255, 255, 255, 235)
BLUE_COLOR = (68, 174, 255, 235)
FINAL_COLOR = (255, 76, 76, 245)
FINAL_FILL = (255, 76, 76, 56)
PANEL_BG = (10, 14, 20, 196)


def render_zone_image_prediction_overlay(prediction: ZoneImagePrediction, source_image: bytes) -> bytes:
    image = ImageOps.exif_transpose(Image.open(BytesIO(source_image))).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _load_font(24)
    small_font = _load_font(18)
    width = max(4, min(image.size) // 180)

    for index, circle in enumerate(prediction.circles[:3], start=1):
        color = SAFE_COLOR if circle.kind == "safe" else BLUE_COLOR
        box = _circle_box(circle.center_x, circle.center_y, circle.radius)
        draw.ellipse(box, outline=color, width=width)
        _draw_label(draw, f"{index}", circle.center_x, circle.center_y - circle.radius - 14, font, color)

    if (
        prediction.final_center_x is not None
        and prediction.final_center_y is not None
        and prediction.final_radius is not None
    ):
        final_box = _circle_box(
            prediction.final_center_x,
            prediction.final_center_y,
            prediction.final_radius,
        )
        draw.ellipse(final_box, fill=FINAL_FILL, outline=FINAL_COLOR, width=width + 1)
        _draw_crosshair(
            draw,
            prediction.final_center_x,
            prediction.final_center_y,
            max(18, prediction.final_radius // 2),
            width,
        )
        x_percent = round(prediction.final_center_x / max(1, prediction.image_width) * 100)
        y_percent = round(prediction.final_center_y / max(1, prediction.image_height) * 100)
        label = f"คาดวงท้าย X{x_percent}% Y{y_percent}%"
        _draw_label(
            draw,
            label,
            prediction.final_center_x,
            prediction.final_center_y + prediction.final_radius + 26,
            small_font,
            FINAL_COLOR,
        )
    else:
        _draw_corner_note(draw, "ยังจับวงจากรูปไม่ได้", font)

    result = Image.alpha_composite(image, overlay).convert("RGB")
    if max(result.size) > MAX_OUTPUT_SIZE:
        result.thumbnail((MAX_OUTPUT_SIZE, MAX_OUTPUT_SIZE), Image.Resampling.LANCZOS)

    output = BytesIO()
    result.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _circle_box(center_x: int, center_y: int, radius: int) -> tuple[int, int, int, int]:
    return center_x - radius, center_y - radius, center_x + radius, center_y + radius


def _draw_crosshair(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    radius: int,
    width: int,
) -> None:
    draw.line((x - radius, y, x + radius, y), fill=FINAL_COLOR, width=width)
    draw.line((x, y - radius, x, y + radius), fill=FINAL_COLOR, width=width)
    draw.ellipse((x - width * 2, y - width * 2, x + width * 2, y + width * 2), fill=FINAL_COLOR)


def _draw_label(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_x: int,
    center_y: int,
    font: ImageFont.FreeTypeFont,
    color: tuple[int, int, int, int],
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    padding_x = 12
    padding_y = 7
    box = (
        center_x - text_width // 2 - padding_x,
        center_y - text_height // 2 - padding_y,
        center_x + text_width // 2 + padding_x,
        center_y + text_height // 2 + padding_y,
    )
    draw.rounded_rectangle(box, radius=8, fill=PANEL_BG, outline=color, width=2)
    draw.text(
        (center_x - text_width / 2, center_y - text_height / 2 - 1),
        text,
        font=font,
        fill=(255, 255, 255, 255),
    )


def _draw_corner_note(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    box = (18, 18, bbox[2] + 44, bbox[3] + 38)
    draw.rounded_rectangle(box, radius=10, fill=PANEL_BG)
    draw.text((31, 26), text, font=font, fill=(255, 255, 255, 255))


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in _font_paths():
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _font_paths() -> tuple[str, ...]:
    candidates = (
        "/System/Library/Fonts/Supplemental/Thonburi.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    return tuple(path for path in candidates if Path(path).exists())
