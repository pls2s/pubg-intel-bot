from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VehicleSpawn:
    name: str
    description: str = ""
    landmarks: list[str] = field(default_factory=list)

    @classmethod
    def from_raw(cls, raw: str | dict[str, Any]) -> "VehicleSpawn":
        if isinstance(raw, str):
            return cls(name=raw, description=f"Vehicle spawn around {raw}.")

        return cls(
            name=str(raw.get("name", "Unknown spawn")),
            description=str(raw.get("description", "")),
            landmarks=[str(item) for item in raw.get("landmarks", [])],
        )


@dataclass(frozen=True)
class LootProfile:
    quality: str = "unknown"
    high_tier_buildings: list[str] = field(default_factory=list)
    route: list[str] = field(default_factory=list)
    notes: str = ""

    @classmethod
    def from_raw(cls, raw: str | dict[str, Any] | None) -> "LootProfile":
        if raw is None:
            return cls()
        if isinstance(raw, str):
            return cls(quality=raw)

        return cls(
            quality=str(raw.get("quality", "unknown")),
            high_tier_buildings=[str(item) for item in raw.get("high_tier_buildings", [])],
            route=[str(item) for item in raw.get("route", [])],
            notes=str(raw.get("notes", "")),
        )


@dataclass(frozen=True)
class Location:
    name: str
    aliases: list[str] = field(default_factory=list)
    vehicles: list[VehicleSpawn] = field(default_factory=list)
    loot: LootProfile = field(default_factory=LootProfile)
    danger: str = "unknown"
    description: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Location":
        # Accept both the production schema ("name") and the compact example
        # schema from the prompt ("location").
        name = raw.get("name") or raw.get("location")
        if not name:
            raise ValueError("Location entry must contain 'name' or 'location'.")

        return cls(
            name=str(name),
            aliases=[str(item) for item in raw.get("aliases", [])],
            vehicles=[VehicleSpawn.from_raw(item) for item in raw.get("vehicles", [])],
            loot=LootProfile.from_raw(raw.get("loot")),
            danger=str(raw.get("danger", "unknown")),
            description=str(raw.get("description", "")),
        )

    @property
    def searchable_terms(self) -> list[str]:
        return [self.name, *self.aliases]


@dataclass(frozen=True)
class SecretRoom:
    name: str
    locations: list[str]
    requirements: str
    loot: str
    notes: str = ""
    aliases: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SecretRoom":
        return cls(
            name=str(raw["name"]),
            locations=[str(item) for item in raw.get("locations", [])],
            requirements=str(raw.get("requirements", "Unknown")),
            loot=str(raw.get("loot", "Unknown")),
            notes=str(raw.get("notes", "")),
            aliases=[str(item) for item in raw.get("aliases", [])],
        )

    @property
    def searchable_terms(self) -> list[str]:
        return [self.name, *self.aliases, *self.locations]


@dataclass(frozen=True)
class DropRecommendations:
    hot: list[str] = field(default_factory=list)
    medium: list[str] = field(default_factory=list)
    safe: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "DropRecommendations":
        raw = raw or {}
        return cls(
            hot=[str(item) for item in raw.get("hot", [])],
            medium=[str(item) for item in raw.get("medium", [])],
            safe=[str(item) for item in raw.get("safe", [])],
        )


@dataclass(frozen=True)
class MapData:
    key: str
    display_name: str
    aliases: list[str]
    locations: list[Location]
    secret_rooms: list[SecretRoom]
    drops: DropRecommendations

    @classmethod
    def from_dict(cls, key: str, raw: dict[str, Any]) -> "MapData":
        return cls(
            key=key,
            display_name=str(raw.get("map", key.title())),
            aliases=[str(item) for item in raw.get("aliases", [])],
            locations=[Location.from_dict(item) for item in raw.get("locations", [])],
            secret_rooms=[SecretRoom.from_dict(item) for item in raw.get("secret_rooms", [])],
            drops=DropRecommendations.from_dict(raw.get("drops")),
        )

    @property
    def searchable_terms(self) -> list[str]:
        return [self.key, self.display_name, *self.aliases]


@dataclass(frozen=True)
class LocationMatch:
    map_data: MapData
    location: Location
    score: float


@dataclass(frozen=True)
class SecretRoomMatch:
    map_data: MapData
    secret_room: SecretRoom
    score: float = 1.0
