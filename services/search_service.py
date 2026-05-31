from __future__ import annotations

from dataclasses import dataclass

from models.map_data import LocationMatch, MapData, SecretRoomMatch
from services.map_service import MapService
from utils.text import normalize_text


@dataclass(frozen=True)
class DropLookup:
    map_data: MapData | None
    risk_hint: str | None = None


class SearchService:
    """Keyword-first search engine prepared for future AI/NLU integration."""

    VEHICLE_KEYWORDS = (
        "vehicle",
        "vehicles",
        "car",
        "cars",
        "truck",
        "garage",
        "spawn",
        "รถ",
        "รถแถว",
        "รถตรง",
        "ยานพาหนะ",
    )
    SECRET_KEYWORDS = (
        "secret",
        "secret room",
        "keycard",
        "key card",
        "security",
        "ห้องลับ",
        "คีย์",
        "คีย์การ์ด",
        "กุญแจ",
    )
    LOOT_KEYWORDS = (
        "loot",
        "high tier",
        "gear",
        "route",
        "ของ",
        "ของดี",
        "ฟาร์ม",
        "ไอเทม",
        "ปืน",
    )
    DROP_KEYWORDS = (
        "drop",
        "hot drop",
        "safe drop",
        "land",
        "landing",
        "ลง",
        "จุดลง",
        "เงียบ",
        "ปลอดภัย",
        "เสี่ยง",
        "ร้อน",
    )
    SAFE_KEYWORDS = ("safe", "quiet", "low risk", "เงียบ", "ปลอดภัย", "คนน้อย")
    HOT_KEYWORDS = ("hot", "fight", "high risk", "ร้อน", "เสี่ยง", "คนเยอะ")
    MEDIUM_KEYWORDS = ("medium", "balanced", "กลาง", "ปานกลาง")

    def __init__(self, map_service: MapService) -> None:
        self.map_service = map_service

    def infer_intent(self, text: str) -> str | None:
        normalized = normalize_text(text)
        if not normalized:
            return None

        # Specific intents are checked before broader loot/drop language.
        checks = (
            ("secret", self.SECRET_KEYWORDS),
            ("vehicle", self.VEHICLE_KEYWORDS),
            ("drop", self.DROP_KEYWORDS),
            ("loot", self.LOOT_KEYWORDS),
        )
        for intent, keywords in checks:
            if self._contains_any(normalized, keywords):
                return intent
        return None

    def vehicle(self, query: str, *, max_results: int = 5) -> list[LocationMatch]:
        return self.map_service.find_locations(
            query,
            require_vehicles=True,
            max_results=max_results,
        )

    def loot(self, query: str, *, max_results: int = 5) -> list[LocationMatch]:
        return self.map_service.find_locations(query, max_results=max_results)

    def secret(self, query: str, *, max_results: int = 8) -> list[SecretRoomMatch]:
        return self.map_service.find_secret_rooms(query, max_results=max_results)

    def drop(self, query: str) -> DropLookup:
        return DropLookup(
            map_data=self.map_service.find_map(query),
            risk_hint=self.extract_risk_hint(query),
        )

    def overview(self, query: str, *, max_results: int = 3) -> list[LocationMatch]:
        return self.map_service.find_locations(query, max_results=max_results)

    def suggestions(self, query: str) -> list[str]:
        return self.map_service.suggestions(query)

    def extract_risk_hint(self, text: str) -> str | None:
        normalized = normalize_text(text)
        if self._contains_any(normalized, self.SAFE_KEYWORDS):
            return "safe"
        if self._contains_any(normalized, self.HOT_KEYWORDS):
            return "hot"
        if self._contains_any(normalized, self.MEDIUM_KEYWORDS):
            return "medium-risk"
        return None

    @staticmethod
    def _contains_any(normalized_text: str, keywords: tuple[str, ...]) -> bool:
        return any(normalize_text(keyword) in normalized_text for keyword in keywords)
