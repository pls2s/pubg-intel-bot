from __future__ import annotations

import base64
import json
import logging
from dataclasses import replace
from io import BytesIO
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from PIL import Image, ImageOps, UnidentifiedImageError

from models.zone import ZoneImagePrediction


logger = logging.getLogger(__name__)

API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
MAX_AI_IMAGE_SIZE = 1400
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TIMEOUT_SECONDS = 30
MAX_OUTPUT_TOKENS = 1200


class GeminiZoneService:
    """Optional Gemini vision layer for screenshot context that heuristics miss."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = DEFAULT_MODEL,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.api_key = api_key
        self.model = _normalize_model(model)
        self.timeout_seconds = max(5, timeout_seconds)

    def refine_prediction(
        self,
        image_bytes: bytes,
        caption: str,
        rule_prediction: ZoneImagePrediction,
    ) -> ZoneImagePrediction:
        if rule_prediction.image_width <= 0 or rule_prediction.image_height <= 0:
            return rule_prediction

        image_data = _image_base64(image_bytes)
        prompt = f"{_system_prompt()}\n\n{_user_prompt(caption, rule_prediction)}"
        raw_response = self._post_generate_content(_request_payload(prompt, image_data))

        raw_text = _extract_text(raw_response)
        if not raw_text:
            logger.warning("Gemini zone response did not include text content")
            return rule_prediction

        try:
            ai_payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.warning("Gemini zone response was not valid JSON: %s", exc)
            return rule_prediction

        return _merge_ai_payload(rule_prediction, ai_payload)

    def _post_generate_content(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{API_BASE_URL}/{quote(self.model, safe='-_.')}:generateContent"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                response_body = response.read()
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"Gemini API returned HTTP {exc.code}: {details}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not connect to Gemini API: {exc.reason}") from exc

        return json.loads(response_body.decode("utf-8"))


def _request_payload(prompt: str, image_data: str) -> dict[str, Any]:
    return {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_data,
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": _response_schema(),
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }


def _system_prompt() -> str:
    return (
        "You are a PUBG: BATTLEGROUNDS zone analyst. Analyze a user-uploaded map "
        "screenshot with safe-zone/blue-zone circles. Provide a practical final-circle "
        "estimate from visual context, not exact server data. Use visible circle positions, "
        "phase/caption hints, water/land splits, terrain, urban cover, roads, and consecutive "
        "circle shift direction. If the image is not a usable PUBG map screenshot, set usable=false. "
        "Return only JSON matching the schema. Use Thai for trend, reason, and tactical_note."
    )


def _user_prompt(caption: str, prediction: ZoneImagePrediction) -> str:
    detected = []
    for index, circle in enumerate(prediction.circles[:4], start=1):
        detected.append(
            {
                "index": index,
                "kind": circle.kind,
                "center_x_percent": round(circle.center_x / max(1, prediction.image_width) * 100, 1),
                "center_y_percent": round(circle.center_y / max(1, prediction.image_height) * 100, 1),
                "radius_percent": round(circle.radius / max(1, min(prediction.image_width, prediction.image_height)) * 100, 1),
            }
        )

    rule_estimate: dict[str, Any] = {}
    if prediction.final_center_x is not None and prediction.final_center_y is not None:
        rule_estimate = {
            "final_x_percent": round(prediction.final_center_x / max(1, prediction.image_width) * 100, 1),
            "final_y_percent": round(prediction.final_center_y / max(1, prediction.image_height) * 100, 1),
            "final_radius_percent": round(
                (prediction.final_radius or 0) / max(1, min(prediction.image_width, prediction.image_height)) * 100,
                1,
            ),
            "trend": prediction.trend,
            "confidence": prediction.confidence,
        }

    context = {
        "caption": caption or "",
        "image_width": prediction.image_width,
        "image_height": prediction.image_height,
        "phase": prediction.phase.phase if prediction.phase else None,
        "rule_based_detected_circles": detected,
        "rule_based_estimate": rule_estimate,
    }
    return (
        "Analyze this PUBG map screenshot and refine the final-zone estimate. "
        "Coordinates must be percentages of the full image: x from left, y from top. "
        "Prefer a usable estimate only when the map/circle context is visible. "
        "Keep trend, reason, and tactical_note in Thai. Keep reason and tactical_note under 120 characters each.\n\n"
        f"Rule-based context JSON:\n{json.dumps(context, ensure_ascii=False)}"
    )


def _response_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "usable": {"type": "boolean", "description": "Whether the image is a usable PUBG zone screenshot."},
            "final_x_percent": {"type": "number", "minimum": 0, "maximum": 100},
            "final_y_percent": {"type": "number", "minimum": 0, "maximum": 100},
            "final_radius_percent": {"type": "number", "minimum": 0, "maximum": 100},
            "confidence": {"type": "string", "enum": ["low", "medium", "medium-high", "high"]},
            "trend": {"type": "string"},
            "reason": {"type": "string"},
            "tactical_note": {"type": "string"},
        },
        "required": [
            "usable",
            "final_x_percent",
            "final_y_percent",
            "final_radius_percent",
            "confidence",
            "trend",
            "reason",
            "tactical_note",
        ],
        "propertyOrdering": [
            "usable",
            "final_x_percent",
            "final_y_percent",
            "final_radius_percent",
            "confidence",
            "trend",
            "reason",
            "tactical_note",
        ],
    }


def _image_base64(image_bytes: bytes) -> str:
    image = _prepare_image(image_bytes)
    output = BytesIO()
    image.save(output, format="JPEG", quality=88, optimize=True)
    return base64.b64encode(output.getvalue()).decode("ascii")


def _prepare_image(image_bytes: bytes) -> Image.Image:
    try:
        image = ImageOps.exif_transpose(Image.open(BytesIO(image_bytes))).convert("RGB")
    except (OSError, UnidentifiedImageError):
        raise ValueError("Could not read image for Gemini zone analysis")

    if max(image.size) > MAX_AI_IMAGE_SIZE:
        image.thumbnail((MAX_AI_IMAGE_SIZE, MAX_AI_IMAGE_SIZE), Image.Resampling.LANCZOS)

    return image


def _extract_text(response: dict[str, Any]) -> str:
    candidates = response.get("candidates") or []
    if not candidates:
        return ""
    parts = ((candidates[0].get("content") or {}).get("parts")) or []
    texts = [str(part.get("text", "")) for part in parts if part.get("text")]
    return "\n".join(texts).strip()


def _merge_ai_payload(
    prediction: ZoneImagePrediction,
    payload: dict[str, Any],
) -> ZoneImagePrediction:
    if not payload.get("usable"):
        notes = [
            *prediction.notes,
            "Gemini ดูแล้วรูปยังไม่ชัดพอสำหรับประเมินบริบท จึงใช้ผล rule-based เดิม",
        ]
        return replace(
            prediction,
            analysis_source="rule-based",
            ai_summary=_clean_text(payload.get("reason", "")),
            notes=_dedupe_notes(notes),
        )

    x_percent = _clamp_float(payload.get("final_x_percent"), 0.0, 100.0)
    y_percent = _clamp_float(payload.get("final_y_percent"), 0.0, 100.0)
    radius_percent = _clamp_float(payload.get("final_radius_percent"), 0.0, 100.0)
    final_x = round(prediction.image_width * x_percent / 100)
    final_y = round(prediction.image_height * y_percent / 100)
    final_radius = round(min(prediction.image_width, prediction.image_height) * radius_percent / 100)

    notes = [
        *prediction.notes,
        "Gemini vision ใช้ช่วยอ่านบริบทจากรูป เช่น ทิศทางวง พื้นที่น้ำ/เมือง/ภูมิประเทศ แล้วปรับจุดคาดการณ์",
    ]

    return replace(
        prediction,
        final_center_x=min(prediction.image_width - 1, max(0, final_x)),
        final_center_y=min(prediction.image_height - 1, max(0, final_y)),
        final_radius=max(8, final_radius) if final_radius else prediction.final_radius,
        trend=_clean_text(payload.get("trend", "")) or prediction.trend,
        confidence=_clean_confidence(str(payload.get("confidence", prediction.confidence))),
        analysis_source="Gemini-assisted",
        ai_summary=_clean_text(payload.get("reason", "")),
        ai_tactical_note=_clean_text(payload.get("tactical_note", "")),
        notes=_dedupe_notes(notes),
    )


def _normalize_model(model: str) -> str:
    normalized = (model or DEFAULT_MODEL).strip()
    if normalized.startswith("models/"):
        normalized = normalized.removeprefix("models/")
    return normalized or DEFAULT_MODEL


def _clamp_float(value: Any, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return minimum
    return min(maximum, max(minimum, number))


def _clean_confidence(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized in {"low", "medium", "medium-high", "high"}:
        return normalized
    return "medium"


def _clean_text(value: Any, limit: int = 260) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def _dedupe_notes(notes: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for note in notes:
        if note in seen:
            continue
        seen.add(note)
        deduped.append(note)
    return deduped
