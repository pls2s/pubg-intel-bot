# PUBG PC Useful Data Plan

Target game: PUBG: BATTLEGROUNDS PC.

Target quality: Useful. The bot should answer quickly with location names, road/building landmarks, risk level, route advice, requirements, loot expectation, source, confidence, and last verified date. It does not need pixel-perfect coordinates yet.

## Source Policy

Use these source levels:

- `official_pubg_map_page`: use for map existence, key landmarks, and official major features.
- `official_patch_notes`: use when a patch changes items, vehicles, secret rooms, loot, map mechanics, or rotations.
- `manual_pc_live_verification`: best source for vehicle spawn points, secret room entrances, loot route quality, and practical drop risk.
- `trusted_community_map`: acceptable for first pass if the URL/source is stored and later spot-checked in game.
- `common_player_knowledge_seed`: temporary seed only. Do not treat as production accurate.

Confidence rules:

- `high`: confirmed in current PC live build or explicitly documented by official PUBG source.
- `medium`: confirmed by at least one trusted source and still plausible in current patch.
- `low`: seed data, old guide, memory, or unverified community claim.

## Official Sources Checked

- PUBG official maps page confirms the current official map pages and featured landmarks for Erangel, Miramar, Sanhok, Taego, Vikendi, and Rondo.
- PUBG official vehicles page confirms the current vehicle catalog.
- PUBG Update 40.1 patch notes confirm that All-In-One Repair Kit, Emergency Cover Flare, and Jammer Pack spawn in Secret Rooms as of Update 40.1, and that Erangel returned from the Subzero variant.

These official pages do not provide complete live coordinates for every vehicle spawn, loot route, or secret-room entrance. Those parts require in-game verification or a trusted map source.

## What I Need From You

For each map, send any of these:

- Full map screenshot with marked points.
- 2D replay screenshot from PUBG Bridge with markers.
- Short clip walking to a secret room or vehicle point.
- Spreadsheet/Google Sheet export with map, location, type, landmark, and notes.
- Link to a community map or guide you trust.

Minimum useful screenshot format:

```text
map: Erangel
type: vehicle | secret_room | loot | drop
location: Pochinki
marker: West Garage
notes: garage road west edge, usually Dacia/UAZ/motorbike line
confidence: high | medium | low
verified_on: 2026-05-31
```

## Data To Collect First

Priority 1:

- Erangel: Pochinki, School, Sosnovka Military Base, Georgopol, Rozhok
- Miramar: Pecado, Hacienda del Patron, Los Leones, Power Grid, Valle del Mar
- Sanhok: Bootcamp, Paradise Resort, Ruins, Camp Alpha, Kampong
- Taego: Terminal, Palace, School, Ho San, Shipyard
- Vikendi: Observatory, Glacier/Lab Camp, Train Station, Lumber Yard, Cave, plus known Secret Rooms
- Rondo: Jadena City, Stadium, NEOX Factory, Rin Jiang, Yu Lin, Mey Ran

Priority 2:

- Add common Thai aliases for every high-traffic callout.
- Add at least 2 vehicle exit options per hot/medium drop.
- Add one recommended squad route and one solo/duo route where they differ.

## Useful-Level JSON Requirements

Every production location should have:

- `name`
- `aliases`
- `vehicles`
- `loot.quality`
- `loot.high_tier_buildings`
- `loot.route`
- `danger`
- `description`
- `verification`

Every vehicle spawn should have:

- `name`
- `description`
- `landmarks`
- `grid` if known
- `verification`

Every secret room should have:

- `name`
- `locations`
- `requirements`
- `loot`
- `notes`
- `verification`

## Current Gaps

The repo currently has working seed data. It is not complete production data yet.

Needs manual/source verification:

- Exact vehicle spawn points and whether they still exist in the current PC live build.
- Exact secret room/security/locked-room locations and requirements per current patch.
- Loot quality by building after recent loot balance changes.
- Drop risk tiers by region/mode/time can vary; use them as tactical guidance, not a promise.
