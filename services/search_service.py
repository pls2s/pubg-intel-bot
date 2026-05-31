from __future__ import annotations

import re
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
        "security room",
        "bear cave",
        "cave",
        "tunnel",
        "underground",
        "bunker",
        "basement",
        "mine",
        "abandoned mine",
        "pagoda",
        "round door",
        "temple",
        "pillar truck",
        "jamila",
        "ห้องลับ",
        "คีย์",
        "คีย์การ์ด",
        "กุญแจ",
        "ถ้ำ",
        "อุโมงค์",
    )
    SECRET_LOOKUP_STOPWORDS = (
        "secret",
        "secret room",
        "keycard",
        "key card",
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
        query = self._strip_keywords(query, self.VEHICLE_KEYWORDS)
        return self.map_service.find_locations(
            query,
            require_vehicles=True,
            max_results=max_results,
        )

    def loot(self, query: str, *, max_results: int = 5) -> list[LocationMatch]:
        query = self._strip_keywords(query, self.LOOT_KEYWORDS)
        return self.map_service.find_locations(query, max_results=max_results)

    def secret(self, query: str, *, max_results: int = 8) -> list[SecretRoomMatch]:
        query = self._strip_keywords(query, self.SECRET_LOOKUP_STOPWORDS)
        return self.map_service.find_secret_rooms(query, max_results=max_results)

    def drop(self, query: str) -> DropLookup:
        lookup_query = self._strip_keywords(query, self.DROP_KEYWORDS)
        return DropLookup(
            map_data=self.map_service.find_map(lookup_query),
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
        return any(SearchService._contains_keyword(normalized_text, keyword) for keyword in keywords)

    @staticmethod
    def _strip_keywords(text: str, keywords: tuple[str, ...]) -> str:
        cleaned = text
        for keyword in sorted(keywords, key=len, reverse=True):
            cleaned = re.sub(
                SearchService._keyword_pattern(keyword),
                " ",
                cleaned,
                flags=re.IGNORECASE,
            )
        cleaned = " ".join(cleaned.split())
        return cleaned or text

    @staticmethod
    def _contains_keyword(normalized_text: str, keyword: str) -> bool:
        keyword_norm = normalize_text(keyword)
        if not keyword_norm:
            return False
        if SearchService._is_ascii_keyword(keyword_norm):
            return re.search(SearchService._keyword_pattern(keyword_norm), normalized_text) is not None
        return keyword_norm in normalized_text

    @staticmethod
    def _keyword_pattern(keyword: str) -> str:
        escaped = re.escape(keyword)
        if SearchService._is_ascii_keyword(keyword):
            return rf"(?<![A-Za-z0-9_]){escaped}(?![A-Za-z0-9_])"
        return escaped

    @staticmethod
    def _is_ascii_keyword(keyword: str) -> bool:
        return bool(re.fullmatch(r"[A-Za-z0-9_ ]+", keyword))
