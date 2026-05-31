from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.gemini_zone_service import GeminiZoneService
from services.map_service import MapService
from services.zone_service import ZoneService
from tools.generate_zone_test_image import DEFAULT_OUTPUT, create_test_zone_image
from utils.formatters import format_zone_image_prediction
from utils.zone_photo_image import render_zone_image_prediction_overlay


DEFAULT_OVERLAY = ROOT / "data" / "test-zone-overlay.png"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Gemini-assisted zone prediction against a local image.")
    parser.add_argument("--image", type=Path, default=DEFAULT_OUTPUT, help="Input screenshot path.")
    parser.add_argument("--overlay", type=Path, default=DEFAULT_OVERLAY, help="Output overlay PNG path.")
    parser.add_argument("--caption", default="phase 5 erangel", help="Caption/context passed to zone analysis.")
    parser.add_argument("--generate", action="store_true", help="Generate the synthetic test image first.")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("GEMINI_API_KEY is not set in .env", file=sys.stderr)
        return 1

    if args.generate or not args.image.exists():
        create_test_zone_image(args.image)

    image_bytes = args.image.read_bytes()
    zone_service = ZoneService(MapService(ROOT / "database"))
    rule_prediction = zone_service.predict_from_image(image_bytes, args.caption)

    gemini_service = GeminiZoneService(
        api_key=api_key,
        model=os.getenv("GEMINI_ZONE_MODEL", "gemini-2.5-flash"),
        timeout_seconds=_int_env("GEMINI_TIMEOUT_SECONDS", 30),
    )
    prediction = gemini_service.refine_prediction(image_bytes, args.caption, rule_prediction)

    args.overlay.parent.mkdir(parents=True, exist_ok=True)
    args.overlay.write_bytes(render_zone_image_prediction_overlay(prediction, image_bytes))

    print(f"image: {args.image}")
    print(f"overlay: {args.overlay}")
    print(f"analysis_source: {prediction.analysis_source}")
    print(f"confidence: {prediction.confidence}")
    print(f"final: {prediction.final_center_x}, {prediction.final_center_y}, r={prediction.final_radius}")
    print("")
    print(format_zone_image_prediction(prediction))
    return 0


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


if __name__ == "__main__":
    raise SystemExit(main())
