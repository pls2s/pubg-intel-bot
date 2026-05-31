from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from models.map_data import LocationMatch, MapData, SecretRoomMatch
from utils.text import normalize_text, similarity


logger = logging.getLogger(__name__)


class MapService:
    """Loads map JSON files and exposes domain-oriented lookup methods."""

    def __init__(self, database_dir: Path | str) -> None:
        self.database_dir = Path(database_dir)
        self.maps: dict[str, MapData] = {}
        self._load_database()

    def _load_database(self) -> None:
        if not self.database_dir.exists():
            raise RuntimeError(f"Map database directory does not exist: {self.database_dir}")

        for path in sorted(self.database_dir.glob("*.json")):
            try:
                map_data = self._load_map_file(path)
            except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
                logger.exception("Skipping invalid map file %s: %s", path, exc)
                continue

            self.maps[map_data.key] = map_data

        if not self.maps:
            raise RuntimeError(f"No valid map JSON files found in {self.database_dir}")

    def _load_map_file(self, path: Path) -> MapData:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Map file root must be a JSON object.")

        key = path.stem.casefold()
        normalized = self._normalize_map_payload(key, raw)
        return MapData.from_dict(key, normalized)

    @staticmethod
    def _normalize_map_payload(key: str, raw: dict[str, Any]) -> dict[str, Any]:
        """Support the compact single-location example and full map files."""

        if "locations" in raw:
            return raw

        if "location" in raw or "name" in raw:
            return {
                "map": raw.get("map", key.title()),
                "aliases": raw.get("map_aliases", []),
                "locations": [raw],
                "secret_rooms": raw.get("secret_rooms", []),
                "drops": raw.get("drops", {}),
            }

        raise ValueError("Map file must contain 'locations' or a single 'location'.")

    def all_map_names(self) -> list[str]:
        return [map_data.display_name for map_data in self.maps.values()]

    def find_map(self, query: str, threshold: float = 0.60) -> MapData | None:
        scored: list[tuple[float, MapData]] = []
        for map_data in self.maps.values():
            score = max(similarity(query, term) for term in map_data.searchable_terms)
            scored.append((score, map_data))

        if not scored:
            return None

        score, map_data = max(scored, key=lambda item: item[0])
        return map_data if score >= threshold else None

    def find_locations(
        self,
        query: str,
        *,
        require_vehicles: bool = False,
        max_results: int = 5,
        threshold: float = 0.52,
    ) -> list[LocationMatch]:
        """Find locations by map name, location name, aliases, and fuzzy text."""

        query_norm = normalize_text(query)
        if not query_norm:
            return []

        matches: list[LocationMatch] = []
        for map_data in self.maps.values():
            map_score = max(similarity(query, term) for term in map_data.searchable_terms)
            map_matched = map_score >= 0.86

            for location in map_data.locations:
                if require_vehicles and not location.vehicles:
                    continue

                location_score = max(similarity(query, term) for term in location.searchable_terms)
                score = max(location_score, min(map_score, 0.75) if map_matched else 0.0)

                if score >= threshold:
                    matches.append(LocationMatch(map_data=map_data, location=location, score=score))

        matches.sort(key=lambda item: item.score, reverse=True)
        return matches[:max_results]

    def find_secret_rooms(self, query: str, *, max_results: int = 8) -> list[SecretRoomMatch]:
        query_norm = normalize_text(query)
        if not query_norm:
            return []

        map_scores = {
            map_data.key: max(similarity(query, term) for term in map_data.searchable_terms)
            for map_data in self.maps.values()
        }
        strong_map_matches = {
            key for key, score in map_scores.items() if score >= 0.86
        }

        candidates: list[tuple[MapData, SecretRoomMatch, float, float]] = []
        for map_data in self.maps.values():
            if strong_map_matches and map_data.key not in strong_map_matches:
                continue

            map_score = map_scores[map_data.key]
            for secret_room in map_data.secret_rooms:
                secret_score = max(similarity(query, term) for term in secret_room.searchable_terms)
                candidates.append(
                    (
                        map_data,
                        SecretRoomMatch(
                            map_data=map_data,
                            secret_room=secret_room,
                            score=secret_score,
                        ),
                        map_score,
                        secret_score,
                    )
                )

        has_specific_room_match = any(secret_score >= 0.68 for _, _, _, secret_score in candidates)

        matches: list[SecretRoomMatch] = []
        for map_data, match, map_score, secret_score in candidates:
            map_matched = map_score >= 0.86

            if has_specific_room_match:
                if secret_score >= 0.68:
                    matches.append(match)
                continue

            score = max(secret_score, min(map_score, 0.8) if map_matched else 0.0)
            if score >= 0.50:
                matches.append(
                    SecretRoomMatch(
                        map_data=map_data,
                        secret_room=match.secret_room,
                        score=score,
                    )
                )

        matches.sort(key=lambda item: item.score, reverse=True)
        return matches[:max_results]

    def suggestions(self, query: str, *, limit: int = 5) -> list[str]:
        candidates: list[tuple[float, str]] = []
        for map_data in self.maps.values():
            map_score = max(similarity(query, term) for term in map_data.searchable_terms)
            candidates.append((map_score, map_data.display_name))

            for location in map_data.locations:
                score = max(similarity(query, term) for term in location.searchable_terms)
                candidates.append((score, f"{location.name} ({map_data.display_name})"))

        candidates.sort(key=lambda item: item[0], reverse=True)

        seen: set[str] = set()
        suggestions: list[str] = []
        for score, label in candidates:
            if score < 0.35 or label in seen:
                continue
            seen.add(label)
            suggestions.append(label)
            if len(suggestions) >= limit:
                break
        return suggestions
