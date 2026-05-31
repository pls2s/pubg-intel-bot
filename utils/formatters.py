from __future__ import annotations

from models.map_data import LocationMatch, MapData, SecretRoomMatch, Verification
from models.zone import ZonePhase, ZonePrediction


VALUE_TH = {
    "unknown": "ไม่ทราบ",
    "low": "ต่ำ",
    "low-medium": "ต่ำ-ปานกลาง",
    "medium": "ปานกลาง",
    "medium-high": "ปานกลาง-สูง",
    "high": "สูง",
    "very high": "สูงมาก",
    "extreme": "สูงสุด",
    "safe": "ปลอดภัย",
    "hot": "เสี่ยงสูง",
    "medium-risk": "เสี่ยงปานกลาง",
}

CONFIDENCE_TH = {
    "high": "สูง",
    "medium": "ปานกลาง",
    "low": "ต่ำ",
}


def th_value(value: str) -> str:
    return VALUE_TH.get(value.casefold(), value)


def th_patch(value: str) -> str:
    patches = {
        "needs manual PC live verification": "รอการตรวจใน PC live",
        "community image transcription": "ถอดข้อมูลจากรูป community",
    }
    return patches.get(value, value)


def format_verification(verification: Verification) -> str:
    if verification.source == "unverified" and verification.confidence == "low":
        return "คุณภาพข้อมูล: ยังไม่ยืนยัน"

    parts = [f"ความมั่นใจ={CONFIDENCE_TH.get(verification.confidence, verification.confidence)}"]
    if verification.last_verified:
        parts.append(f"ตรวจล่าสุด={verification.last_verified}")
    if verification.patch:
        parts.append(f"แพตช์/แหล่งอ้างอิง={th_patch(verification.patch)}")
    return f"คุณภาพข้อมูล: {', '.join(parts)}"


def usage(command: str, examples: list[str]) -> str:
    lines = [f"วิธีใช้: /{command} <ชื่อแผนที่หรือสถานที่>", "", "ตัวอย่าง:"]
    lines.extend(f"- {example}" for example in examples)
    return "\n".join(lines)


def format_not_found(topic: str, query: str, suggestions: list[str] | None = None) -> str:
    lines = [
        f"ไม่พบข้อมูล {topic} สำหรับ: {query}",
        "ลองพิมพ์ชื่อแผนที่หรือสถานที่ เช่น Pochinki, School, Erangel, Vikendi, Taego, Miramar หรือ Rondo",
    ]
    if suggestions:
        lines.append("")
        lines.append("รายการที่ใกล้เคียง:")
        lines.extend(f"- {item}" for item in suggestions[:5])
    return "\n".join(lines)


def format_vehicle_results(matches: list[LocationMatch]) -> str:
    blocks: list[str] = []
    for match in matches:
        location = match.location
        lines = [
            f"จุดเกิดรถ: {location.name} ({match.map_data.display_name})",
            f"ความเสี่ยง: {th_value(location.danger)}",
            format_verification(location.verification),
        ]
        if location.description:
            lines.append(f"ข้อมูล: {location.description}")
        lines.append("")
        for spawn in location.vehicles:
            lines.append(f"- {spawn.name}")
            if spawn.grid:
                lines.append(f"  กริด: {spawn.grid}")
            if spawn.description:
                lines.append(f"  {spawn.description}")
            if spawn.landmarks:
                lines.append(f"  จุดสังเกต: {', '.join(spawn.landmarks)}")
            if spawn.verification.source != "unverified":
                lines.append(f"  {format_verification(spawn.verification)}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def format_secret_results(matches: list[SecretRoomMatch]) -> str:
    blocks: list[str] = []
    for match in matches:
        room = match.secret_room
        lines = [
            f"ห้องลับ/จุดพิเศษ: {room.name} ({match.map_data.display_name})",
            f"สิ่งที่ต้องใช้: {room.requirements}",
            f"ของที่คาดว่าจะเจอ: {room.loot}",
            format_verification(room.verification),
        ]
        if room.notes:
            lines.append(f"หมายเหตุ: {room.notes}")
        lines.append("ตำแหน่ง:")
        lines.extend(f"- {item}" for item in room.locations)
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def format_secret_image_caption(match: SecretRoomMatch) -> str:
    room = match.secret_room
    lines = [
        f"แผนที่ตำแหน่ง: {room.name} ({match.map_data.display_name})",
        f"สิ่งที่ต้องใช้: {room.requirements}",
        f"จำนวนตำแหน่งในฐานข้อมูล: {len(room.locations)} จุด",
        format_verification(room.verification),
    ]
    return "\n".join(lines)[:1000]


def format_loot_results(matches: list[LocationMatch]) -> str:
    blocks: list[str] = []
    for match in matches:
        location = match.location
        loot = location.loot
        lines = [
            f"ข้อมูล loot: {location.name} ({match.map_data.display_name})",
            f"คุณภาพ loot: {th_value(loot.quality)}",
            f"ความเสี่ยง: {th_value(location.danger)}",
            format_verification(loot.verification if loot.verification.source != "unverified" else location.verification),
        ]
        if location.description:
            lines.append(f"ข้อมูล: {location.description}")
        if loot.high_tier_buildings:
            lines.append("")
            lines.append("อาคาร/จุด loot ดี:")
            lines.extend(f"- {item}" for item in loot.high_tier_buildings)
        if loot.route:
            lines.append("")
            lines.append("เส้นทาง loot แนะนำ:")
            lines.extend(f"{index}. {item}" for index, item in enumerate(loot.route, start=1))
        if loot.notes:
            lines.append("")
            lines.append(f"หมายเหตุ: {loot.notes}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def format_drop_recommendation(map_data: MapData, risk_hint: str | None = None) -> str:
    drops = map_data.drops
    lines = [f"แนะนำจุดลง: {map_data.display_name}"]
    lines.append(format_verification(drops.verification if drops.verification.source != "unverified" else map_data.verification))
    if risk_hint:
        lines.append(f"โฟกัส: {th_value(risk_hint)}")
    lines.append("")

    sections = [
        ("จุดลงร้อน/เสี่ยงสูง", drops.hot),
        ("จุดลงเสี่ยงปานกลาง", drops.medium),
        ("จุดลงปลอดภัยกว่า", drops.safe),
    ]
    for title, items in sections:
        lines.append(f"{title}:")
        lines.extend(f"- {item}" for item in items or ["ยังไม่มีข้อมูล"])
        lines.append("")

    return "\n".join(lines).strip()


def format_zone_prediction(prediction: ZonePrediction) -> str:
    lines: list[str] = ["ทำนายวง PUBG"]

    if prediction.map_data:
        lines.append(f"แผนที่: {prediction.map_data.display_name}")
    else:
        lines.append("แผนที่: ยังไม่ได้ระบุ")

    if prediction.phase:
        lines.append(format_zone_phase_line(prediction.phase))
        lines.append(f"คำแนะนำ phase นี้: {prediction.phase.guidance}")
    else:
        lines.append("Phase: ยังไม่ได้ระบุ")

    lines.append(f"ความมั่นใจ: {th_value(prediction.confidence)}")

    if prediction.anchors:
        lines.append(f"จุดอ้างอิงจากข้อความ: {', '.join(prediction.anchors)}")

    if prediction.candidates:
        lines.append("")
        lines.append("พื้นที่ที่น่าจบ/ควรระวัง:")
        for index, candidate in enumerate(prediction.candidates, start=1):
            lines.append(f"{index}. {candidate.name} - ประมาณ {candidate.probability}%")
            lines.append(f"   เหตุผล: {candidate.reason}")
            lines.append(f"   ควรเล่น: {candidate.action}")
    else:
        lines.append("")
        lines.append("ยังทำนายพื้นที่ไม่ได้ เพราะต้องมีชื่อแผนที่อย่างน้อย")

    if prediction.notes:
        lines.append("")
        lines.append("หมายเหตุ:")
        lines.extend(f"- {note}" for note in prediction.notes)

    return "\n".join(lines)


def format_zone_phase_line(phase: ZonePhase) -> str:
    return (
        f"Phase {phase.phase}: รอก่อนบีบ {format_duration(phase.wait_seconds)}, "
        f"บีบ {format_duration(phase.shrink_seconds)}, "
        f"ดาเมจ {phase.damage_per_second:g} HP/sec"
    )


def format_zone_phase_table(phases: list[ZonePhase]) -> str:
    lines = ["ข้อมูลวง PUBG ตาม phase"]
    for phase in phases:
        lines.append("")
        lines.append(format_zone_phase_line(phase))
        lines.append(f"คำแนะนำ: {phase.guidance}")
    lines.append("")
    lines.append("ใช้ /zone <map> phase <เลข> <จุดที่วงกิน> เพื่อทำนายพื้นที่วงท้าย")
    return "\n".join(lines)


def format_duration(seconds: int) -> str:
    minutes, remainder = divmod(seconds, 60)
    if minutes and remainder:
        return f"{minutes}น {remainder}วิ"
    if minutes:
        return f"{minutes}น"
    return f"{remainder}วิ"


def format_map_overview(match: LocationMatch) -> str:
    location = match.location
    lines = [
        f"{location.name} ({match.map_data.display_name})",
        f"ความเสี่ยง: {th_value(location.danger)}",
        f"คุณภาพ loot: {th_value(location.loot.quality)}",
    ]
    if location.description:
        lines.append(f"ข้อมูล: {location.description}")
    if location.vehicles:
        lines.append(f"จุดเกิดรถ: มีข้อมูล {len(location.vehicles)} จุด")
    return "\n".join(lines)
