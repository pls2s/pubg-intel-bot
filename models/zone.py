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


@dataclass(frozen=True)
class ZoneImageCircle:
    center_x: int
    center_y: int
    radius: int
    kind: str = "safe"
    confidence: float = 0.0


@dataclass(frozen=True)
class ZoneImagePrediction:
    image_width: int
    image_height: int
    phase: ZonePhase | None = None
    circles: list[ZoneImageCircle] = field(default_factory=list)
    final_center_x: int | None = None
    final_center_y: int | None = None
    final_radius: int | None = None
    trend: str = ""
    confidence: str = "low"
    analysis_source: str = "rule-based"
    ai_summary: str = ""
    ai_tactical_note: str = ""
    notes: list[str] = field(default_factory=list)
