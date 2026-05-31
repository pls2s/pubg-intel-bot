from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATABASE_DIR = ROOT / "database"
REQUIRED_LOCATION_FIELDS = ("name", "loot", "danger", "description", "verification")
REQUIRED_LOOT_FIELDS = ("quality", "high_tier_buildings", "route")
REQUIRED_VEHICLE_FIELDS = ("name", "description", "landmarks")


def main() -> int:
    errors: list[str] = []
    for path in sorted(DATABASE_DIR.glob("*.json")):
        if path.parent.name == "templates":
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON: {exc}")
            continue

        errors.extend(validate_map(path, raw))

    if errors:
        print("Database validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Database validation passed.")
    return 0


def validate_map(path: Path, raw: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("map", "aliases", "locations", "drops", "verification"):
        if field not in raw:
            errors.append(f"{path}: missing root field '{field}'")

    for index, location in enumerate(raw.get("locations", [])):
        label = f"{path}: locations[{index}]"
        for field in REQUIRED_LOCATION_FIELDS:
            if field not in location:
                errors.append(f"{label}: missing '{field}'")

        loot = location.get("loot", {})
        if isinstance(loot, dict):
            for field in REQUIRED_LOOT_FIELDS:
                if field not in loot:
                    errors.append(f"{label}.loot: missing '{field}'")
        else:
            errors.append(f"{label}.loot: must be an object for useful-level data")

        for vehicle_index, vehicle in enumerate(location.get("vehicles", [])):
            vehicle_label = f"{label}.vehicles[{vehicle_index}]"
            if isinstance(vehicle, str):
                errors.append(f"{vehicle_label}: string vehicle entries are seed-only; use object entries")
                continue
            for field in REQUIRED_VEHICLE_FIELDS:
                if field not in vehicle:
                    errors.append(f"{vehicle_label}: missing '{field}'")

    for index, room in enumerate(raw.get("secret_rooms", [])):
        label = f"{path}: secret_rooms[{index}]"
        for field in ("name", "locations", "requirements", "loot", "verification"):
            if field not in room:
                errors.append(f"{label}: missing '{field}'")

    return errors


if __name__ == "__main__":
    sys.exit(main())
