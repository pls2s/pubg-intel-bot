from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from models.zone import ZoneCandidate, ZonePrediction


WIDTH = 1200
HEIGHT = 900
MARGIN = 44
MAP_X0 = 48
MAP_Y0 = 138
MAP_SIZE = 704
PANEL_X0 = 792
PANEL_Y0 = 138
PANEL_W = 360
PANEL_H = 704

BG = (16, 20, 26)
PANEL = (29, 35, 45)
PANEL_2 = (35, 42, 54)
TEXT = (239, 243, 246)
MUTED = (167, 178, 190)
GRID = (72, 86, 101)
WATER = (24, 77, 96)
LAND = (45, 79, 62)
ROAD = (162, 153, 133)
WHITE = (255, 255, 255)
ACCENT = (255, 185, 76)
COLORS = [
    (255, 94, 91),
    (255, 190, 72),
    (78, 205, 196),
    (119, 201, 101),
    (151, 123, 255),
]


def render_zone_prediction_image(prediction: ZonePrediction) -> bytes:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    fonts = _load_fonts()

    _draw_header(draw, prediction, fonts)
    _draw_map_panel(image, draw, prediction, fonts)
    _draw_side_panel(draw, prediction, fonts)
    _draw_footer(draw, fonts)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _draw_header(draw: ImageDraw.ImageDraw, prediction: ZonePrediction, fonts: dict[str, ImageFont.FreeTypeFont]) -> None:
    title = "PUBG Zone Prediction"
    subtitle_parts = []
    if prediction.map_data:
        subtitle_parts.append(prediction.map_data.display_name)
    if prediction.phase:
        subtitle_parts.append(f"Phase {prediction.phase.phase}")
    subtitle = " | ".join(subtitle_parts) or "Rule-based prediction"

    draw.text((MARGIN, 36), title, font=fonts["title"], fill=TEXT)
    draw.text((MARGIN, 92), subtitle, font=fonts["body"], fill=MUTED)

    confidence = f"Confidence: {prediction.confidence}"
    badge_w = _text_width(draw, confidence, fonts["small"]) + 32
    draw.rounded_rectangle((WIDTH - badge_w - MARGIN, 44, WIDTH - MARGIN, 86), radius=18, fill=(48, 59, 75))
    draw.text((WIDTH - badge_w - MARGIN + 16, 54), confidence, font=fonts["small"], fill=ACCENT)


def _draw_map_panel(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    prediction: ZonePrediction,
    fonts: dict[str, ImageFont.FreeTypeFont],
) -> None:
    draw.rounded_rectangle((MAP_X0, MAP_Y0, MAP_X0 + MAP_SIZE, MAP_Y0 + MAP_SIZE), radius=18, fill=PANEL)

    map_box = (MAP_X0 + 24, MAP_Y0 + 24, MAP_X0 + MAP_SIZE - 24, MAP_Y0 + MAP_SIZE - 24)
    draw.rounded_rectangle(map_box, radius=12, fill=LAND)
    _draw_terrain(draw, map_box)
    _draw_grid(draw, map_box, fonts)

    if prediction.candidates:
        _draw_candidate_heat(image, draw, map_box, prediction.candidates, fonts)
    else:
        message = "Add a map name to generate prediction areas"
        _draw_centered_text(draw, map_box, message, fonts["body"], MUTED)

    if prediction.anchors:
        anchors = ", ".join(prediction.anchors[:3])
        draw.rounded_rectangle((MAP_X0 + 40, MAP_Y0 + MAP_SIZE - 78, MAP_X0 + MAP_SIZE - 40, MAP_Y0 + MAP_SIZE - 34), radius=14, fill=(20, 26, 34))
        draw.text((MAP_X0 + 58, MAP_Y0 + MAP_SIZE - 68), f"Anchors: {anchors}", font=fonts["small"], fill=TEXT)

    label = prediction.map_data.display_name if prediction.map_data else "No map selected"
    draw.text((MAP_X0 + 44, MAP_Y0 + 42), label, font=fonts["panel_title"], fill=TEXT)
    draw.text((MAP_X0 + 44, MAP_Y0 + 82), "schematic heatmap", font=fonts["small"], fill=MUTED)


def _draw_terrain(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle((x0, y0, x1, y0 + 92), fill=(35, 84, 89))
    draw.rectangle((x0, y1 - 78, x1, y1), fill=(35, 84, 89))
    draw.polygon(
        [
            (x0 + 60, y1 - 30),
            (x0 + 156, y0 + 120),
            (x0 + 262, y0 + 96),
            (x0 + 340, y1 - 70),
            (x0 + 420, y0 + 146),
            (x1 - 80, y0 + 80),
            (x1 - 120, y1 - 40),
        ],
        fill=(61, 93, 73),
    )
    draw.line((x0 + 44, y0 + 420, x1 - 60, y0 + 198), fill=ROAD, width=7)
    draw.line((x0 + 120, y1 - 90, x1 - 124, y0 + 120), fill=ROAD, width=6)
    draw.line((x0 + 80, y0 + 210, x1 - 90, y1 - 120), fill=ROAD, width=5)
    for offset in (95, 190, 285, 380, 475):
        draw.ellipse((x0 + offset, y0 + offset // 3 + 80, x0 + offset + 36, y0 + offset // 3 + 116), fill=(72, 105, 76))


def _draw_grid(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fonts: dict[str, ImageFont.FreeTypeFont]) -> None:
    x0, y0, x1, y1 = box
    for index in range(1, 5):
        x = x0 + (x1 - x0) * index // 5
        y = y0 + (y1 - y0) * index // 5
        draw.line((x, y0, x, y1), fill=GRID, width=1)
        draw.line((x0, y, x1, y), fill=GRID, width=1)
    draw.text(((x0 + x1) // 2 - 8, y0 + 8), "N", font=fonts["small"], fill=MUTED)
    draw.text(((x0 + x1) // 2 - 8, y1 - 32), "S", font=fonts["small"], fill=MUTED)
    draw.text((x0 + 12, (y0 + y1) // 2 - 10), "W", font=fonts["small"], fill=MUTED)
    draw.text((x1 - 28, (y0 + y1) // 2 - 10), "E", font=fonts["small"], fill=MUTED)


def _draw_candidate_heat(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    candidates: list[ZoneCandidate],
    fonts: dict[str, ImageFont.FreeTypeFont],
) -> None:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    for index, candidate in enumerate(candidates[:5]):
        color = COLORS[index % len(COLORS)]
        x, y = _candidate_point(candidate.name, index, box)
        radius = 42 + candidate.probability
        overlay_draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=(*color, 72),
            outline=(*color, 170),
            width=4,
        )
        inner = 28
        overlay_draw.ellipse((x - inner, y - inner, x + inner, y + inner), fill=(*color, 232))

    image.alpha_composite(overlay) if image.mode == "RGBA" else image.paste(Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB"))

    for index, candidate in enumerate(candidates[:5]):
        color = COLORS[index % len(COLORS)]
        x, y = _candidate_point(candidate.name, index, box)
        label = str(index + 1)
        bbox = draw.textbbox((0, 0), label, font=fonts["marker"])
        draw.text(
            (x - (bbox[2] - bbox[0]) / 2, y - (bbox[3] - bbox[1]) / 2 - 3),
            label,
            font=fonts["marker"],
            fill=WHITE,
        )
        draw.rounded_rectangle((x - 46, y + 38, x + 46, y + 72), radius=12, fill=(18, 22, 29))
        percent = f"{candidate.probability}%"
        _draw_centered_text(draw, (x - 46, y + 38, x + 46, y + 72), percent, fonts["tiny"], color)


def _draw_side_panel(draw: ImageDraw.ImageDraw, prediction: ZonePrediction, fonts: dict[str, ImageFont.FreeTypeFont]) -> None:
    draw.rounded_rectangle((PANEL_X0, PANEL_Y0, PANEL_X0 + PANEL_W, PANEL_Y0 + PANEL_H), radius=18, fill=PANEL)

    y = PANEL_Y0 + 28
    draw.text((PANEL_X0 + 26, y), "Summary", font=fonts["panel_title"], fill=TEXT)
    y += 48

    if prediction.phase:
        phase = prediction.phase
        phase_lines = [
            f"Phase {phase.phase}",
            f"Wait {_format_duration_en(phase.wait_seconds)}",
            f"Shrink {_format_duration_en(phase.shrink_seconds)}",
            f"Damage {phase.damage_per_second:g} HP/sec",
        ]
    else:
        phase_lines = ["Phase not provided"]

    y = _draw_info_box(draw, PANEL_X0 + 22, y, PANEL_W - 44, "Circle", phase_lines, fonts)
    y += 18

    if prediction.candidates:
        draw.text((PANEL_X0 + 26, y), "Likely end zones", font=fonts["body_bold"], fill=TEXT)
        y += 36
        for index, candidate in enumerate(prediction.candidates[:5]):
            color = COLORS[index % len(COLORS)]
            draw.rounded_rectangle((PANEL_X0 + 24, y + 3, PANEL_X0 + 54, y + 33), radius=10, fill=color)
            _draw_centered_text(draw, (PANEL_X0 + 24, y + 3, PANEL_X0 + 54, y + 33), str(index + 1), fonts["tiny"], WHITE)
            draw.text((PANEL_X0 + 66, y), candidate.name[:28], font=fonts["small"], fill=TEXT)
            draw.text((PANEL_X0 + 66, y + 25), f"Approx {candidate.probability}%", font=fonts["tiny"], fill=MUTED)
            y += 64
    else:
        y = _draw_info_box(draw, PANEL_X0 + 22, y, PANEL_W - 44, "Need more data", ["Add map name, e.g. Erangel", "Add phase and circle area"], fonts)


def _draw_info_box(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    width: int,
    title: str,
    lines: list[str],
    fonts: dict[str, ImageFont.FreeTypeFont],
) -> int:
    height = 38 + len(lines) * 28 + 16
    draw.rounded_rectangle((x, y, x + width, y + height), radius=14, fill=PANEL_2)
    draw.text((x + 18, y + 14), title, font=fonts["small_bold"], fill=ACCENT)
    current_y = y + 48
    for line in lines:
        draw.text((x + 18, current_y), line, font=fonts["small"], fill=TEXT)
        current_y += 28
    return y + height


def _draw_footer(draw: ImageDraw.ImageDraw, fonts: dict[str, ImageFont.FreeTypeFont]) -> None:
    note = "Schematic heatmap from rule-based prediction | not server circle data"
    draw.text((MARGIN, HEIGHT - 38), note, font=fonts["tiny"], fill=MUTED)


def _candidate_point(name: str, index: int, box: tuple[int, int, int, int]) -> tuple[int, int]:
    x0, y0, x1, y1 = box
    text = name.casefold()
    x = 0.5
    y = 0.5

    if any(word in text for word in ("west", "georgopol", "valle", "alpha", "bashara", "capaco")):
        x -= 0.25
    if any(word in text for word in ("east", "mylta", "leones", "terminal", "shipyard", "neox", "assembly", "atahul")):
        x += 0.25
    if any(word in text for word in ("north", "cosmodrome", "hacienda", "paradise", "shipyard", "al habar", "lab")):
        y -= 0.25
    if any(word in text for word in ("south", "sosnovka", "quarry", "ho san", "yu lin", "al hayik")):
        y += 0.25
    if any(word in text for word in ("river", "water", "bridge")):
        y += 0.08

    offsets = ((-0.03, -0.02), (0.04, 0.03), (0.01, -0.05), (-0.05, 0.06), (0.06, -0.01))
    dx, dy = offsets[index % len(offsets)]
    x = min(0.86, max(0.14, x + dx))
    y = min(0.86, max(0.14, y + dy))
    return int(x0 + (x1 - x0) * x), int(y0 + (y1 - y0) * y)


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
) -> None:
    x0, y0, x1, y1 = box
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    draw.text((x0 + (x1 - x0 - width) / 2, y0 + (y1 - y0 - height) / 2 - 2), text, font=font, fill=fill)


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _format_duration_en(seconds: int) -> str:
    minutes, remainder = divmod(seconds, 60)
    if minutes and remainder:
        return f"{minutes}m {remainder}s"
    if minutes:
        return f"{minutes}m"
    return f"{remainder}s"


def _load_fonts() -> dict[str, ImageFont.FreeTypeFont]:
    regular = _font_path()
    bold = _font_path(bold=True) or regular
    return {
        "title": _load_font(regular, 44),
        "panel_title": _load_font(bold, 28),
        "body": _load_font(regular, 25),
        "body_bold": _load_font(bold, 24),
        "small": _load_font(regular, 19),
        "small_bold": _load_font(bold, 19),
        "tiny": _load_font(regular, 15),
        "marker": _load_font(bold, 29),
    }


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default(size=size)


def _font_path(*, bold: bool = False) -> str:
    candidates = [
        "/System/Library/Fonts/Supplemental/Thonburi.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return ""
