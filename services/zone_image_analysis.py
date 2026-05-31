from __future__ import annotations

from collections.abc import Iterable
from io import BytesIO
from math import atan2, hypot, pi

from PIL import Image, ImageOps, UnidentifiedImageError

from models.zone import ZoneImageCircle, ZoneImagePrediction, ZonePhase


MAX_ANALYSIS_SIZE = 900
ANGLE_BUCKETS = 48
FINAL_RADIUS_BY_PHASE = {
    1: 0.10,
    2: 0.13,
    3: 0.18,
    4: 0.25,
    5: 0.36,
    6: 0.52,
    7: 0.72,
    8: 0.95,
    9: 1.0,
}
SHIFT_WEIGHT_BY_PHASE = {
    1: 0.25,
    2: 0.30,
    3: 0.38,
    4: 0.45,
    5: 0.50,
    6: 0.35,
    7: 0.20,
    8: 0.08,
    9: 0.0,
}


def analyze_zone_image(image_bytes: bytes, phase: ZonePhase | None = None) -> ZoneImagePrediction:
    try:
        image = ImageOps.exif_transpose(Image.open(BytesIO(image_bytes))).convert("RGB")
    except (OSError, UnidentifiedImageError):
        return ZoneImagePrediction(
            image_width=0,
            image_height=0,
            notes=["อ่านไฟล์รูปไม่ได้ ลองส่งเป็นรูปภาพ PNG/JPG อีกครั้ง"],
        )

    original_width, original_height = image.size
    scale = min(1.0, MAX_ANALYSIS_SIZE / max(original_width, original_height))
    analysis_image = image
    if scale < 1.0:
        analysis_size = (max(1, int(original_width * scale)), max(1, int(original_height * scale)))
        analysis_image = image.resize(analysis_size, Image.Resampling.LANCZOS)

    raw_circles = _detect_circles(analysis_image)
    circles = _scale_circles(raw_circles, scale)
    primary = _primary_circle(circles)

    if not primary:
        return ZoneImagePrediction(
            image_width=original_width,
            image_height=original_height,
            phase=phase,
            circles=circles,
            notes=[
                "ยังจับเส้นวงจากรูปไม่ได้",
                "ลอง crop ให้เห็นแผนที่ชัด ๆ และให้เส้นวงสีขาว/ฟ้าอยู่ในภาพ",
                "ใส่ phase ใน caption เช่น phase 4 หรือ วง 4 เพื่อช่วยประเมินวงท้าย",
            ],
        )

    outer = _outer_circle(primary, circles)
    final_radius = max(8, int(primary.radius * _final_radius_factor(primary, phase, original_width, original_height)))
    final_x, final_y = _project_final_center(primary, outer, final_radius, phase)
    final_x = min(original_width - 1, max(0, final_x))
    final_y = min(original_height - 1, max(0, final_y))

    trend = _trend_label(primary, outer)
    confidence = _confidence_label(primary, outer, phase)
    notes = [
        "เป็นการเดาจากรูปวงและทิศทางการดึง ไม่ใช่ข้อมูลวงจริงจาก server",
        "ถ้ารูปมีวงเดียว ระบบจะใช้จุดกลางวงนั้นเป็นฐาน แล้วให้ความมั่นใจต่ำกว่า",
    ]
    if phase is None:
        notes.append("ใส่ phase ใน caption เช่น phase 4 หรือ วง 4 จะช่วยให้ขนาดวงท้ายสมเหตุผลขึ้น")
    if outer:
        notes.append("พบวงมากกว่าหนึ่งวง จึงใช้แนวจากวงใหญ่ไปวงเล็กช่วยคาดทิศทาง")

    return ZoneImagePrediction(
        image_width=original_width,
        image_height=original_height,
        phase=phase,
        circles=circles,
        final_center_x=final_x,
        final_center_y=final_y,
        final_radius=final_radius,
        trend=trend,
        confidence=confidence,
        notes=notes,
    )


def _detect_circles(image: Image.Image) -> list[ZoneImageCircle]:
    width, height = image.size
    white_mask, blue_mask = _build_masks(image)

    candidates: list[ZoneImageCircle] = []
    candidates.extend(_components_to_circles(white_mask, width, height, "safe"))
    candidates.extend(_components_to_circles(blue_mask, width, height, "blue"))
    candidates.sort(key=lambda circle: circle.confidence, reverse=True)
    return _dedupe_circles(candidates)[:5]


def _build_masks(image: Image.Image) -> tuple[bytearray, bytearray]:
    width, height = image.size
    pixels = image.load()
    white_mask = bytearray(width * height)
    blue_mask = bytearray(width * height)

    for y in range(height):
        row_offset = y * width
        for x in range(width):
            r, g, b = pixels[x, y]
            if _is_white_zone_pixel(r, g, b):
                white_mask[row_offset + x] = 1
            elif _is_blue_zone_pixel(r, g, b):
                blue_mask[row_offset + x] = 1

    return white_mask, blue_mask


def _is_white_zone_pixel(r: int, g: int, b: int) -> bool:
    return r >= 188 and g >= 188 and b >= 188 and max(r, g, b) - min(r, g, b) <= 72


def _is_blue_zone_pixel(r: int, g: int, b: int) -> bool:
    return b >= 145 and g >= 80 and b - r >= 45 and b >= g - 8


def _components_to_circles(mask: bytearray, width: int, height: int, kind: str) -> list[ZoneImageCircle]:
    visited = bytearray(width * height)
    circles: list[ZoneImageCircle] = []
    min_diameter = max(44, int(min(width, height) * 0.075))

    for start, value in enumerate(mask):
        if not value or visited[start]:
            continue

        points: list[tuple[int, int]] = []
        stack = [start]
        visited[start] = 1
        xmin = xmax = start % width
        ymin = ymax = start // width

        while stack:
            index = stack.pop()
            x = index % width
            y = index // width
            points.append((x, y))
            xmin = min(xmin, x)
            xmax = max(xmax, x)
            ymin = min(ymin, y)
            ymax = max(ymax, y)

            for neighbor in _neighbors(index, x, y, width, height):
                if mask[neighbor] and not visited[neighbor]:
                    visited[neighbor] = 1
                    stack.append(neighbor)

        circle = _component_to_circle(points, xmin, ymin, xmax, ymax, min_diameter, kind)
        if circle:
            circles.append(circle)

    return circles


def _neighbors(index: int, x: int, y: int, width: int, height: int) -> Iterable[int]:
    if x > 0:
        yield index - 1
    if x < width - 1:
        yield index + 1
    if y > 0:
        yield index - width
        if x > 0:
            yield index - width - 1
        if x < width - 1:
            yield index - width + 1
    if y < height - 1:
        yield index + width
        if x > 0:
            yield index + width - 1
        if x < width - 1:
            yield index + width + 1


def _component_to_circle(
    points: list[tuple[int, int]],
    xmin: int,
    ymin: int,
    xmax: int,
    ymax: int,
    min_diameter: int,
    kind: str,
) -> ZoneImageCircle | None:
    count = len(points)
    box_width = xmax - xmin + 1
    box_height = ymax - ymin + 1
    if box_width < min_diameter or box_height < min_diameter:
        return None

    aspect = min(box_width, box_height) / max(box_width, box_height)
    if aspect < 0.62:
        return None

    fill_ratio = count / (box_width * box_height)
    if fill_ratio > 0.34:
        return None

    center_x = (xmin + xmax) / 2
    center_y = (ymin + ymax) / 2
    radius = (box_width + box_height) / 4
    if radius <= 0:
        return None

    sample_step = max(1, count // 900)
    sample = points[::sample_step]
    distances = [hypot(x - center_x, y - center_y) for x, y in sample]
    average_distance = sum(distances) / len(distances)
    variance = sum((distance - average_distance) ** 2 for distance in distances) / len(distances)
    radial_noise = (variance**0.5) / max(average_distance, 1.0)
    radius_error = abs(average_distance - radius) / radius
    angular_coverage = _angular_coverage(sample, center_x, center_y)

    if radial_noise > 0.36 or radius_error > 0.32 or angular_coverage < 0.34:
        return None

    aspect_score = aspect
    ring_score = _ring_fill_score(fill_ratio)
    radial_score = max(0.0, 1.0 - radial_noise / 0.36)
    radius_score = max(0.0, 1.0 - radius_error / 0.32)
    coverage_score = min(1.0, angular_coverage / 0.80)
    kind_score = 1.0 if kind == "safe" else 0.92
    confidence = (
        0.24 * aspect_score
        + 0.18 * ring_score
        + 0.23 * radial_score
        + 0.15 * radius_score
        + 0.20 * coverage_score
    ) * kind_score

    if confidence < 0.34:
        return None

    return ZoneImageCircle(
        center_x=round(center_x),
        center_y=round(center_y),
        radius=max(1, round(radius)),
        kind=kind,
        confidence=round(confidence, 3),
    )


def _angular_coverage(points: list[tuple[int, int]], center_x: float, center_y: float) -> float:
    buckets: set[int] = set()
    for x, y in points:
        angle = atan2(y - center_y, x - center_x)
        bucket = int(((angle + pi) / (2 * pi)) * ANGLE_BUCKETS)
        buckets.add(min(ANGLE_BUCKETS - 1, max(0, bucket)))
    return len(buckets) / ANGLE_BUCKETS


def _ring_fill_score(fill_ratio: float) -> float:
    if 0.006 <= fill_ratio <= 0.12:
        return 1.0
    if fill_ratio < 0.006:
        return max(0.0, fill_ratio / 0.006)
    return max(0.0, 1.0 - (fill_ratio - 0.12) / 0.22)


def _dedupe_circles(circles: list[ZoneImageCircle]) -> list[ZoneImageCircle]:
    deduped: list[ZoneImageCircle] = []
    for circle in circles:
        duplicate_index = _duplicate_index(circle, deduped)
        if duplicate_index is None:
            deduped.append(circle)
            continue

        existing = deduped[duplicate_index]
        if _prefer_circle(circle, existing):
            deduped[duplicate_index] = circle
    deduped.sort(key=lambda item: item.confidence, reverse=True)
    return deduped


def _duplicate_index(circle: ZoneImageCircle, existing: list[ZoneImageCircle]) -> int | None:
    for index, other in enumerate(existing):
        radius_delta = abs(circle.radius - other.radius) / max(circle.radius, other.radius)
        center_delta = hypot(circle.center_x - other.center_x, circle.center_y - other.center_y)
        if radius_delta <= 0.16 and center_delta <= max(14, max(circle.radius, other.radius) * 0.12):
            return index
    return None


def _prefer_circle(candidate: ZoneImageCircle, current: ZoneImageCircle) -> bool:
    if candidate.kind == "safe" and current.kind != "safe" and candidate.confidence >= current.confidence * 0.9:
        return True
    return candidate.confidence > current.confidence


def _scale_circles(circles: list[ZoneImageCircle], scale: float) -> list[ZoneImageCircle]:
    if scale >= 1.0:
        return circles
    return [
        ZoneImageCircle(
            center_x=round(circle.center_x / scale),
            center_y=round(circle.center_y / scale),
            radius=max(1, round(circle.radius / scale)),
            kind=circle.kind,
            confidence=circle.confidence,
        )
        for circle in circles
    ]


def _primary_circle(circles: list[ZoneImageCircle]) -> ZoneImageCircle | None:
    if not circles:
        return None
    top_confidence = circles[0].confidence
    strong = [circle for circle in circles if circle.confidence >= max(0.40, top_confidence * 0.72)]
    return min(strong or circles, key=lambda circle: circle.radius)


def _outer_circle(primary: ZoneImageCircle, circles: list[ZoneImageCircle]) -> ZoneImageCircle | None:
    larger = [
        circle
        for circle in circles
        if circle is not primary and circle.radius >= primary.radius * 1.18
    ]
    if not larger:
        return None
    return min(larger, key=lambda circle: hypot(circle.center_x - primary.center_x, circle.center_y - primary.center_y))


def _final_radius_factor(
    primary: ZoneImageCircle,
    phase: ZonePhase | None,
    image_width: int,
    image_height: int,
) -> float:
    if phase:
        return FINAL_RADIUS_BY_PHASE.get(phase.phase, 0.35)

    radius_ratio = primary.radius / max(1, min(image_width, image_height))
    if radius_ratio > 0.32:
        return 0.12
    if radius_ratio > 0.23:
        return 0.18
    if radius_ratio > 0.16:
        return 0.27
    if radius_ratio > 0.11:
        return 0.40
    if radius_ratio > 0.08:
        return 0.58
    return 0.78


def _project_final_center(
    primary: ZoneImageCircle,
    outer: ZoneImageCircle | None,
    final_radius: int,
    phase: ZonePhase | None,
) -> tuple[int, int]:
    if not outer:
        return primary.center_x, primary.center_y

    dx = primary.center_x - outer.center_x
    dy = primary.center_y - outer.center_y
    shift_distance = hypot(dx, dy)
    if shift_distance < max(10, primary.radius * 0.12):
        return primary.center_x, primary.center_y

    weight = SHIFT_WEIGHT_BY_PHASE.get(phase.phase, 0.35) if phase else 0.38
    projected_x = primary.center_x + dx * weight
    projected_y = primary.center_y + dy * weight

    allowed_distance = max(0, primary.radius - final_radius)
    projected_distance = hypot(projected_x - primary.center_x, projected_y - primary.center_y)
    if allowed_distance and projected_distance > allowed_distance:
        scale = allowed_distance / projected_distance
        projected_x = primary.center_x + (projected_x - primary.center_x) * scale
        projected_y = primary.center_y + (projected_y - primary.center_y) * scale

    return round(projected_x), round(projected_y)


def _trend_label(primary: ZoneImageCircle, outer: ZoneImageCircle | None) -> str:
    if not outer:
        return "กลางวงที่ตรวจพบ"

    dx = primary.center_x - outer.center_x
    dy = primary.center_y - outer.center_y
    if hypot(dx, dy) < max(10, primary.radius * 0.12):
        return "กลางวงเดิม"

    horizontal = ""
    vertical = ""
    if dx > primary.radius * 0.10:
        horizontal = "ขวา"
    elif dx < -primary.radius * 0.10:
        horizontal = "ซ้าย"
    if dy > primary.radius * 0.10:
        vertical = "ล่าง"
    elif dy < -primary.radius * 0.10:
        vertical = "บน"

    return "".join((vertical, horizontal)) or "กลางวงเดิม"


def _confidence_label(primary: ZoneImageCircle, outer: ZoneImageCircle | None, phase: ZonePhase | None) -> str:
    score = primary.confidence
    if outer:
        score += 0.10
    if phase:
        score += 0.08

    if score >= 0.76:
        return "medium-high"
    if score >= 0.55:
        return "medium"
    return "low"
