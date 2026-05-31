from __future__ import annotations

from models.map_data import LocationMatch, MapData, SecretRoomMatch


def usage(command: str, examples: list[str]) -> str:
    lines = [f"Usage: /{command} <map or location>", "", "Examples:"]
    lines.extend(f"- {example}" for example in examples)
    return "\n".join(lines)


def format_not_found(topic: str, query: str, suggestions: list[str] | None = None) -> str:
    lines = [
        f"I could not find {topic} data for: {query}",
        "Try a map or location name, for example Pochinki, School, Erangel, Vikendi, or Taego.",
    ]
    if suggestions:
        lines.append("")
        lines.append("Closest matches:")
        lines.extend(f"- {item}" for item in suggestions[:5])
    return "\n".join(lines)


def format_vehicle_results(matches: list[LocationMatch]) -> str:
    blocks: list[str] = []
    for match in matches:
        location = match.location
        lines = [
            f"Vehicle spawns for {location.name} ({match.map_data.display_name})",
            f"Danger: {location.danger}",
        ]
        if location.description:
            lines.append(f"Intel: {location.description}")
        lines.append("")
        for spawn in location.vehicles:
            lines.append(f"- {spawn.name}")
            if spawn.description:
                lines.append(f"  {spawn.description}")
            if spawn.landmarks:
                lines.append(f"  Landmarks: {', '.join(spawn.landmarks)}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def format_secret_results(matches: list[SecretRoomMatch]) -> str:
    blocks: list[str] = []
    for match in matches:
        room = match.secret_room
        lines = [
            f"Secret room: {room.name} ({match.map_data.display_name})",
            f"Requirements: {room.requirements}",
            f"Loot: {room.loot}",
        ]
        if room.notes:
            lines.append(f"Notes: {room.notes}")
        lines.append("Locations:")
        lines.extend(f"- {item}" for item in room.locations)
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def format_loot_results(matches: list[LocationMatch]) -> str:
    blocks: list[str] = []
    for match in matches:
        location = match.location
        loot = location.loot
        lines = [
            f"Loot intel for {location.name} ({match.map_data.display_name})",
            f"Quality: {loot.quality}",
            f"Danger: {location.danger}",
        ]
        if location.description:
            lines.append(f"Intel: {location.description}")
        if loot.high_tier_buildings:
            lines.append("")
            lines.append("High-tier buildings:")
            lines.extend(f"- {item}" for item in loot.high_tier_buildings)
        if loot.route:
            lines.append("")
            lines.append("Recommended route:")
            lines.extend(f"{index}. {item}" for index, item in enumerate(loot.route, start=1))
        if loot.notes:
            lines.append("")
            lines.append(f"Notes: {loot.notes}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def format_drop_recommendation(map_data: MapData, risk_hint: str | None = None) -> str:
    drops = map_data.drops
    lines = [f"Drop recommendations for {map_data.display_name}"]
    if risk_hint:
        lines.append(f"Focus: {risk_hint}")
    lines.append("")

    sections = [
        ("Hot drops", drops.hot),
        ("Medium-risk drops", drops.medium),
        ("Safe drops", drops.safe),
    ]
    for title, items in sections:
        lines.append(f"{title}:")
        lines.extend(f"- {item}" for item in items or ["No data yet"])
        lines.append("")

    return "\n".join(lines).strip()


def format_map_overview(match: LocationMatch) -> str:
    location = match.location
    lines = [
        f"{location.name} ({match.map_data.display_name})",
        f"Danger: {location.danger}",
        f"Loot: {location.loot.quality}",
    ]
    if location.description:
        lines.append(f"Intel: {location.description}")
    if location.vehicles:
        lines.append(f"Vehicle spawns: {len(location.vehicles)} known")
    return "\n".join(lines)
