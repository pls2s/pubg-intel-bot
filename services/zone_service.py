from __future__ import annotations

import re
from dataclasses import dataclass

from models.map_data import Location, MapData
from models.zone import ZoneCandidate, ZonePhase, ZonePrediction
from services.map_service import MapService
from utils.text import normalize_text, similarity


@dataclass(frozen=True)
class CandidateProfile:
    name: str
    tags: tuple[str, ...]
    base_weight: int
    reason: str
    action: str


class ZoneService:
    """Rule-based zone assistant prepared for telemetry/ML upgrades later."""

    ZONE_KEYWORDS = (
        "zone",
        "circle",
        "blue",
        "bluezone",
        "safe zone",
        "phase",
        "predict",
        "prediction",
        "วง",
        "วงบีบ",
        "วงท้าย",
        "วงสุดท้าย",
        "ทำนายวง",
        "เฟส",
        "บลูโซน",
    )

    PHASES: dict[int, ZonePhase] = {
        1: ZonePhase(1, 330, 270, 0.6, "มีเวลาฟาร์มและหารถ แต่ควรวางแผนทางเข้าไว้แล้ว"),
        2: ZonePhase(2, 90, 120, 0.8, "เริ่ม rotate เข้าขอบวงหรือ compound ที่เล่นต่อได้"),
        3: ZonePhase(3, 60, 120, 1.0, "เริ่มเลือกพื้นที่ยืนจริง อย่าเสียรถง่าย"),
        4: ZonePhase(4, 60, 120, 3.0, "ต้องมี cover หรือรถพร้อมเข้า ดาเมจเริ่มลงโทษหนัก"),
        5: ZonePhase(5, 60, 120, 5.0, "อย่าเล่นไกลวง ถ้าไม่มีรถให้เข้า edge ก่อน"),
        6: ZonePhase(6, 60, 120, 8.0, "ให้ความสำคัญกับ hard cover, ridge, smoke และมุมเข้า"),
        7: ZonePhase(7, 60, 90, 10.0, "พื้นที่เล่นเหลือน้อย ตัดสินใจเร็วและเลี่ยง open field"),
        8: ZonePhase(8, 60, 60, 14.0, "จบไฟต์เป็นหลัก ดาเมจวงแทบไม่ให้แก้ตัว"),
        9: ZonePhase(9, 10, 160, 18.0, "วงปิดสุดท้าย ต้องเล่นตำแหน่งและ utility ให้คุ้มที่สุด"),
    }

    MAP_PROFILES: dict[str, tuple[CandidateProfile, ...]] = {
        "erangel": (
            CandidateProfile(
                "School / Apartment ridge",
                ("center", "ridge", "compound", "urban", "school"),
                78,
                "พื้นที่กลางแผนที่ มี ridge และ compound ให้เล่นต่อหลายเฟส",
                "ยึดอาคารหรือเนินก่อนวง 4 แล้วเตรียม smoke ถ้าวงดึง open field",
            ),
            CandidateProfile(
                "Rozhok hill / Water Town edge",
                ("center", "ridge", "compound", "rozhok"),
                72,
                "คุมทางผ่านกลาง Erangel ได้ดีและมีมุมเล่นขอบน้ำ",
                "อย่าลงต่ำในเมืองนาน ถ้าวงดึงเนินให้รีบกิน high ground",
            ),
            CandidateProfile(
                "East Pochinki fields",
                ("center", "field", "compound", "pochinki"),
                64,
                "วงกลางที่กิน Pochinki มักบังคับเล่นบ้านเล็กและร่องดินรอบเมือง",
                "เลือก compound ขอบเมือง อย่าขับผ่านกลางเมืองตอนวง 4+",
            ),
            CandidateProfile(
                "Farm / Mylta fields",
                ("east", "field", "compound", "mylta", "farm"),
                55,
                "ฝั่งตะวันออกมี open field เยอะ แต่มีบ้านเล็กให้ chain rotate",
                "เก็บรถไว้ให้ครบทีมและเล่นขอบวงด้านที่มีรั้วหรือเนิน",
            ),
            CandidateProfile(
                "Sosnovka west ridge",
                ("south", "island", "ridge", "bridge", "military"),
                50,
                "ถ้าวงลงเกาะ โซน ridge ฝั่งตะวันตกเล่นง่ายกว่า open runway",
                "เข้าก่อน bridge ถูกล็อก แล้วคุม ridge แทนการแช่ฐานทัพ",
            ),
            CandidateProfile(
                "Georgopol / Hospital ridge",
                ("west", "north", "ridge", "urban", "georgopol"),
                48,
                "มีเมืองใหญ่และเนินให้ยืน แต่ rotation จากใต้ขึ้นมายาก",
                "เลือกฝั่งเมืองให้ชัดและอย่าเสียเวลาใน container ถ้าวงบีบออก",
            ),
        ),
        "miramar": (
            CandidateProfile(
                "Pecado / Arena ridges",
                ("center", "ridge", "urban", "pecado"),
                76,
                "กลาง Miramar มักตัดสินด้วย ridge รอบเมืองและเส้นถนน",
                "ยึดเนินขอบเมืองก่อน ไม่ควรติดใน Arena ตอนวง 5+",
            ),
            CandidateProfile(
                "Hacienda / San Martin hills",
                ("center", "north", "ridge", "compound", "hacienda"),
                69,
                "เนินรอบ Hacienda คุม sightline ได้กว้าง",
                "อย่าเข้าทางโล่งตรงกลาง ให้ใช้ ridge บังรถ",
            ),
            CandidateProfile(
                "Los Leones edges",
                ("east", "urban", "compound", "los", "leones"),
                62,
                "เมืองใหญ่ให้ cover เยอะ แต่ถ้าวงหลุดเมืองจะออกยาก",
                "เล่นขอบเมืองด้านวงต่อไป อย่าติดตึกชั้นล่างนาน",
            ),
            CandidateProfile(
                "Power Grid / Minas ridges",
                ("center", "west", "ridge", "compound", "power"),
                58,
                "โซนนี้มีเนินและ compound สลับกัน เหมาะกับทีมมีรถ",
                "ถือ high ground แล้วใช้รถสำหรับย้ายข้าม open gap",
            ),
            CandidateProfile(
                "Valle del Mar bridge side",
                ("south", "west", "bridge", "urban", "valle"),
                46,
                "ถ้าวงกินใต้ การข้ามสะพานและ cliff จะเป็นตัวตัดทีม",
                "เข้าก่อนและตัดสินใจว่าจะเล่นฝั่งเมืองหรือฝั่งเนิน",
            ),
        ),
        "sanhok": (
            CandidateProfile(
                "Bootcamp center",
                ("center", "urban", "compound", "bootcamp"),
                82,
                "Sanhok วงกลางมักบังคับไฟต์เร็วและมี third party สูง",
                "ยึดอาคาร/กำแพง อย่าข้าม open courtyard ตอนวงบีบ",
            ),
            CandidateProfile(
                "Paradise Resort hills",
                ("north", "ridge", "compound", "paradise"),
                68,
                "เนินรอบ Paradise ให้ข้อมูลและมุมกดทีมที่ rotate",
                "เล่นขอบรีสอร์ตหรือเนิน ไม่ควรติดในห้องถ้าวงดึงออก",
            ),
            CandidateProfile(
                "Pai Nan river edge",
                ("center", "river", "urban", "edge"),
                56,
                "แม่น้ำทำให้ทางเข้าแคบและคาดเดา rotation ได้ง่าย",
                "เลือกฝั่งแม่น้ำให้เร็ว อย่าข้ามตอนวง 5+",
            ),
            CandidateProfile(
                "Quarry ridges",
                ("south", "ridge", "field", "quarry"),
                52,
                "Quarry มีระดับความสูงหลายชั้น แต่ cover บางช่วงบาง",
                "ใช้เนินเป็น cover และเตรียม utility สำหรับดันขึ้นชั้นสูง",
            ),
            CandidateProfile(
                "Camp Alpha / ruins west",
                ("west", "compound", "ridge", "alpha", "ruins"),
                48,
                "ฝั่งตะวันตกมี compound สั้นๆ ต่อกัน เหมาะกับ edge play",
                "เล่นช้าได้แค่ต้นเกม เลทเกมต้องเข้า cover ก่อน",
            ),
        ),
        "vikendi": (
            CandidateProfile(
                "Castle / Train Station approach",
                ("center", "urban", "bridge", "castle"),
                70,
                "พื้นที่กลางมีทางเข้าแคบและ cover แข็งหลายจุด",
                "เลือกฝั่งสะพานให้ชัด อย่าถูกบีบให้ว่ายน้ำหรือข้ามโล่ง",
            ),
            CandidateProfile(
                "Villa / winery fields",
                ("east", "field", "compound", "villa"),
                60,
                "บ้านและไร่องุ่นให้ cover กระจาย แต่ open gap เยอะ",
                "ใช้รถเก็บระยะและเลือก compound ที่มีทางออกสองด้าน",
            ),
            CandidateProfile(
                "Dino Park / Lumber Yard edge",
                ("west", "compound", "field", "dino"),
                57,
                "ฝั่งตะวันตกมีอาคารเล็กและ open field สลับกัน",
                "เล่นขอบวงพร้อมรถ อย่าดันเข้ากลาง field ช้าเกินไป",
            ),
            CandidateProfile(
                "Cosmodrome south hills",
                ("north", "ridge", "compound", "cosmodrome"),
                55,
                "เนินรอบ Cosmodrome คุมเส้นทางเข้าได้ดี",
                "อยู่บน high ground แต่เตรียมย้ายถ้าวงดึงลงเมือง",
            ),
            CandidateProfile(
                "Cement Factory ridges",
                ("north", "ridge", "industrial", "cement"),
                50,
                "พื้นที่โรงงานมี cover ใหญ่แต่ sightline ยาว",
                "เลี่ยงการ rotate กลางถนน เปิดมุมยิงก่อนย้าย",
            ),
        ),
        "taego": (
            CandidateProfile(
                "School / central fields",
                ("center", "field", "compound", "school"),
                72,
                "กลาง Taego มีบ้านเล็กและทุ่งกว้าง เหมาะกับทีมที่เก็บรถไว้",
                "จับ compound ก่อนวง 4 แล้วใช้รถเป็น cover สำรอง",
            ),
            CandidateProfile(
                "Palace / Go Dok approach",
                ("west", "compound", "urban", "palace"),
                62,
                "โซนตะวันตกมีเมืองกับเนินสั้นให้เล่นหลายชั้น",
                "อย่าติดในเมืองใหญ่ถ้าวงดึงออก ให้กินขอบก่อน",
            ),
            CandidateProfile(
                "Terminal / Buk San Sa fields",
                ("east", "field", "compound", "terminal"),
                58,
                "ทุ่งกว้างและถนนยาวทำให้รถสำคัญมาก",
                "หมุนเร็วและเลือก compound มากกว่าจอดกลาง field",
            ),
            CandidateProfile(
                "Ho San / Song Am south",
                ("south", "urban", "compound", "hosan"),
                54,
                "ฝั่งใต้มีเมืองและทางเข้าเป็นคอขวดบางจุด",
                "เข้าก่อนทีมอื่นและกันมุมหลังจากสะพาน/ถนนหลัก",
            ),
            CandidateProfile(
                "Shipyard north-east ridge",
                ("north", "east", "ridge", "shipyard"),
                46,
                "ถ้าวงดึงเหนือ เส้นทางขึ้นช้าและถูกมองเห็นง่าย",
                "ใช้ขอบแผนที่และเข้า high ground ก่อนวงบีบ",
            ),
        ),
        "rondo": (
            CandidateProfile(
                "Jadena City edges",
                ("center", "urban", "compound", "jadena"),
                72,
                "เมืองใหญ่มี cover เยอะ แต่การออกจากเมืองช่วงท้ายยาก",
                "เล่นขอบเมืองด้านวงต่อไป อย่าติดกลางเมืองตอนวง 5+",
            ),
            CandidateProfile(
                "Stadium / Arena approach",
                ("center", "urban", "compound", "stadium"),
                64,
                "พื้นที่สนามมีอาคารใหญ่และ open gap รอบนอก",
                "เลือกมุมออกล่วงหน้าและเก็บ smoke สำหรับข้ามถนน",
            ),
            CandidateProfile(
                "Rin Jiang river edge",
                ("river", "urban", "edge", "rinjiang"),
                56,
                "แม่น้ำและสะพานบังคับทางเข้า ทำให้คุม rotation ได้",
                "ตัดสินใจฝั่งน้ำตั้งแต่ก่อนวง 4",
            ),
            CandidateProfile(
                "Yu Lin south hills",
                ("south", "ridge", "compound", "yulin"),
                52,
                "เนินใต้ให้มุมมองดี แต่โดนบีบลง open ได้ง่าย",
                "ถือ ridge ที่มีทางถอย ไม่ยืน skyline นาน",
            ),
            CandidateProfile(
                "Neox Factory service roads",
                ("east", "industrial", "compound", "neox"),
                48,
                "โรงงานและถนนบริการให้ cover สั้นๆ สำหรับ late rotate",
                "เล่นมุมอาคารและระวังทีมที่ตัดจากถนนหลัก",
            ),
        ),
        "deston": (
            CandidateProfile(
                "Lodge / Arena fields",
                ("center", "compound", "field", "lodge", "arena"),
                68,
                "พื้นที่กลางมี compound ใหญ่และ open gap",
                "เข้าก่อนแล้วกันทีมที่ rotate จาก field",
            ),
            CandidateProfile(
                "Assembly east approach",
                ("east", "urban", "compound", "assembly"),
                58,
                "เมืองและถนนด้านตะวันออกทำให้ทางเข้าเดาง่าย",
                "เลือกอาคารขอบเมืองและเตรียมออกถ้าวงดึง field",
            ),
            CandidateProfile(
                "Hydroelectric Dam ridges",
                ("west", "ridge", "water", "dam"),
                54,
                "น้ำและสันเขาบังคับเส้นทางเดิน",
                "อย่าถูกบีบให้ข้ามน้ำช้า เก็บ high ground ก่อน",
            ),
            CandidateProfile(
                "Construction / Turita roads",
                ("center", "compound", "road", "construction"),
                50,
                "ถนนและสิ่งปลูกสร้างช่วย chain rotation ได้",
                "เก็บรถไว้ใกล้ cover และเลี่ยงจอดกลางถนน",
            ),
        ),
        "karakin": (
            CandidateProfile(
                "Al Habar / north ridge",
                ("north", "ridge", "urban", "alhabar"),
                68,
                "Karakin เล็กและโล่ง การถือ ridge สำคัญมาก",
                "เลี่ยง skyline และใช้ throwable เปิดทาง",
            ),
            CandidateProfile(
                "Bashara / west town edge",
                ("west", "urban", "compound", "bashara"),
                60,
                "บ้านฝั่งตะวันตกให้ cover แต่ rotate ข้ามเขายาก",
                "เล่นขอบเมืองและอย่าออกช้าเมื่อวงดึงกลาง",
            ),
            CandidateProfile(
                "Al Hayik south approach",
                ("south", "urban", "compound", "alhayik"),
                56,
                "ทางใต้มีเมืองเล็กและเนินต่อเนื่อง",
                "คุมมุมขึ้นเนินและอย่าข้าม open ตอนวง 5+",
            ),
            CandidateProfile(
                "Central tunnel ridges",
                ("center", "ridge", "tunnel", "compound"),
                52,
                "อุโมงค์และเนินกลางช่วยเปลี่ยนมุมเล่นได้",
                "ใช้ tunnel เป็นทางเลือก แต่ต้องระวังทีมดักทางออก",
            ),
        ),
        "paramo": (
            CandidateProfile(
                "Helipad center",
                ("center", "compound", "field", "helipad"),
                70,
                "Paramo มี layout เปลี่ยนได้ จึงควรอ่านจากจุดกลางปัจจุบัน",
                "เลือก compound ที่ใกล้วงและมีทางลงเขาหลายด้าน",
            ),
            CandidateProfile(
                "Lab / north hills",
                ("north", "ridge", "compound", "lab"),
                60,
                "เนินสูงทำให้คุม rotation ได้ แต่โดนบีบลงเขาเร็ว",
                "ถือ high ground เท่าที่วงอนุญาตและเตรียมทางถอย",
            ),
            CandidateProfile(
                "Capaco west edge",
                ("west", "urban", "compound", "capaco"),
                56,
                "เมืองให้ cover แต่เส้นทางออกอาจถูก lock",
                "อย่าแช่ในเมืองถ้าวงดึงออก ให้กินขอบก่อน",
            ),
            CandidateProfile(
                "Atahul east approach",
                ("east", "compound", "field", "atahual"),
                52,
                "ฝั่งตะวันออกมีบ้านกระจายและ open gap",
                "เก็บ utility สำหรับข้ามช่องโล่ง",
            ),
        ),
    }

    DIRECTION_KEYWORDS = {
        "north": ("north", "เหนือ", "บน"),
        "south": ("south", "ใต้", "ล่าง"),
        "east": ("east", "ตะวันออก", "ขวา"),
        "west": ("west", "ตะวันตก", "ซ้าย"),
        "center": ("center", "central", "กลาง"),
        "edge": ("edge", "ขอบ"),
        "water": ("water", "river", "น้ำ", "แม่น้ำ"),
    }

    PHASE_RE = re.compile(r"(?:phase|p|เฟส|วง)\s*([1-9])(?!\d)", re.IGNORECASE)

    def __init__(self, map_service: MapService) -> None:
        self.map_service = map_service

    def predict(self, query: str) -> ZonePrediction:
        cleaned_query = self._strip_zone_keywords(query)
        phase = self.phase_for_text(query)
        map_data = self._infer_map(cleaned_query)

        if not map_data:
            notes = ["ระบุชื่อแผนที่เพื่อให้ทำนายพื้นที่ได้ เช่น Erangel, Miramar, Taego"]
            return ZonePrediction(query=query, phase=phase, confidence="low", notes=notes)

        anchors = self._find_anchor_locations(cleaned_query, map_data)
        hints = self._extract_hints(query)
        candidates = self._rank_candidates(map_data, phase, anchors, hints)
        confidence = self._confidence(phase, anchors, hints)
        notes = [
            "เป็นการประเมินจาก pattern วงและตำแหน่งบนแผนที่ ไม่ใช่การรู้ค่าจาก server",
            "ยิ่งกรอก phase 3-5 และชื่อจุดที่วงกินอยู่ ผลจะมีประโยชน์ขึ้น",
        ]
        return ZonePrediction(
            query=query,
            map_data=map_data,
            phase=phase,
            anchors=[location.name for location in anchors],
            candidates=candidates,
            confidence=confidence,
            notes=notes,
        )

    def phase_for_text(self, text: str) -> ZonePhase | None:
        match = self.PHASE_RE.search(text)
        if not match:
            return None
        return self.PHASES.get(int(match.group(1)))

    def all_phases(self) -> list[ZonePhase]:
        return [self.PHASES[index] for index in sorted(self.PHASES)]

    def _infer_map(self, query: str) -> MapData | None:
        map_data = self.map_service.find_map(query)
        if map_data:
            return map_data

        location_matches = self.map_service.find_locations(query, max_results=3, threshold=0.78)
        return location_matches[0].map_data if location_matches else None

    def _find_anchor_locations(self, query: str, map_data: MapData) -> list[Location]:
        normalized_query = normalize_text(query)
        scored: list[tuple[float, Location]] = []

        for location in map_data.locations:
            scores: list[float] = []
            for term in location.searchable_terms:
                normalized_term = normalize_text(term)
                if not normalized_term:
                    continue
                if normalized_term in normalized_query and len(normalized_term) >= 3:
                    scores.append(1.0)
                elif self._has_prefix_match(normalized_query, normalized_term):
                    scores.append(0.86)
                else:
                    scores.append(similarity(query, term))

            score = max(scores, default=0.0)
            if score >= 0.68:
                scored.append((score, location))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [location for _, location in scored[:3]]

    def _extract_hints(self, query: str) -> set[str]:
        normalized_query = normalize_text(query)
        hints: set[str] = set()
        for hint, keywords in self.DIRECTION_KEYWORDS.items():
            if any(normalize_text(keyword) in normalized_query for keyword in keywords):
                hints.add(hint)
        return hints

    @staticmethod
    def _has_prefix_match(normalized_query: str, normalized_term: str) -> bool:
        query_tokens = {token for token in normalized_query.split() if len(token) >= 3}
        term_tokens = {token for token in normalized_term.split() if len(token) >= 4}
        return any(term.startswith(query) for query in query_tokens for term in term_tokens)

    def _rank_candidates(
        self,
        map_data: MapData,
        phase: ZonePhase | None,
        anchors: list[Location],
        hints: set[str],
    ) -> list[ZoneCandidate]:
        profiles = self.MAP_PROFILES.get(map_data.key, ())
        if not profiles:
            profiles = self._profiles_from_locations(map_data)

        scored: list[tuple[int, CandidateProfile]] = []
        anchor_terms = {normalize_text(anchor.name) for anchor in anchors}
        for anchor in anchors:
            anchor_terms.update(normalize_text(alias) for alias in anchor.aliases)

        for profile in profiles:
            score = profile.base_weight
            profile_text = normalize_text(" ".join((profile.name, *profile.tags)))

            for anchor in anchor_terms:
                if anchor and anchor in profile_text:
                    score += 34
                elif anchor and any(token in profile.tags for token in anchor.split()):
                    score += 12

            for hint in hints:
                if hint in profile.tags:
                    score += 16

            if phase:
                if phase.phase >= 5 and {"ridge", "compound", "urban"} & set(profile.tags):
                    score += 12
                if phase.phase >= 5 and "field" in profile.tags:
                    score -= 8
                if phase.phase <= 2 and "center" in profile.tags:
                    score += 8

            scored.append((max(score, 1), profile))

        scored.sort(key=lambda item: item[0], reverse=True)
        top = scored[:5]
        total = sum(score for score, _ in top) or 1

        return [
            ZoneCandidate(
                name=profile.name,
                probability=max(1, round(score / total * 100)),
                reason=profile.reason,
                action=profile.action,
            )
            for score, profile in top
        ]

    def _profiles_from_locations(self, map_data: MapData) -> tuple[CandidateProfile, ...]:
        profiles: list[CandidateProfile] = []
        for location in map_data.locations[:6]:
            profiles.append(
                CandidateProfile(
                    name=location.name,
                    tags=("compound",),
                    base_weight=50,
                    reason="ใช้จุดสำคัญในฐานข้อมูลเป็น candidate ชั่วคราว",
                    action="กรอก phase และจุดกลางวงเพิ่มเพื่อให้คำแนะนำแคบลง",
                )
            )
        return tuple(profiles)

    def _confidence(self, phase: ZonePhase | None, anchors: list[Location], hints: set[str]) -> str:
        score = 0
        if phase:
            score += 1
            if phase.phase >= 3:
                score += 1
        if anchors:
            score += 2
        if hints:
            score += 1

        if score >= 4:
            return "medium-high"
        if score >= 2:
            return "medium"
        return "low"

    def _strip_zone_keywords(self, text: str) -> str:
        cleaned = text
        for keyword in sorted(self.ZONE_KEYWORDS, key=len, reverse=True):
            cleaned = re.sub(
                self._keyword_pattern(keyword),
                " ",
                cleaned,
                flags=re.IGNORECASE,
            )
        return " ".join(cleaned.split()) or text

    @staticmethod
    def _keyword_pattern(keyword: str) -> str:
        escaped = re.escape(keyword)
        if re.fullmatch(r"[A-Za-z0-9_ ]+", keyword):
            return rf"(?<![A-Za-z0-9_]){escaped}(?![A-Za-z0-9_])"
        return escaped
