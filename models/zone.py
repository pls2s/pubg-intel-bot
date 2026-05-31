from __future__ import annotations

from dataclasses import dataclass, field

from models.map_data import MapData


@dataclass(frozen=True)
class ZonePhase:
    phase: int
    wait_seconds: int
    shrink_seconds: int
    damage_per_second: float
    guidance: str


@dataclass(frozen=True)
class ZoneCandidate:
    name: str
    probability: int
    reason: str
    action: str


@dataclass(frozen=True)
class ZonePrediction:
    query: str
    map_data: MapData | None = None
    phase: ZonePhase | None = None
    anchors: list[str] = field(default_factory=list)
    candidates: list[ZoneCandidate] = field(default_factory=list)
    confidence: str = "low"
    notes: list[str] = field(default_factory=list)
