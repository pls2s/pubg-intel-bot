# Secret Room Source Research

Scope: PUBG: BATTLEGROUNDS PC, Useful-level data.

Last research pass: 2026-05-31.

## Sources Reviewed

### Steam guide: UPDATED: The Location of the Secret Rooms

URL: https://steamcommunity.com/sharedfiles/filedetails/?id=3583051048

Status: newer community guide, not official.

Posted: 2025-10-08.

Updated: 2026-05-25.

What it provides:

- Erangel, Miramar, Taego, Rondo, Deston, Vikendi, and Paramo secret/security room maps.
- It explicitly says locations were manually verified in August-October 2025 and May 2026.
- It documents key names per map:
  - Erangel: Secret Basement Key
  - Miramar: Secret Room Key
  - Taego: Secret Key
  - Rondo: Secret Room Key
  - Deston: Security Key
  - Vikendi: Security Key
  - Paramo: Secret Room Key
- It includes reference screenshots for room entrance types such as Miramar abandoned mines, Rondo pagodas with round doors, Deston trucks, Vikendi bunkers, and Paramo golden-door temples.

Use in database:

- Mark as `steam_community_guide` with `confidence=medium`.
- It supersedes the older Reddit image set where the map exists in both sources, because it is explicitly updated in May 2026.
- Promote individual locations to `confidence=high` only after PC live/custom match or PUBG Bridge verification.

Integrated into JSON:

- Added Miramar Secret Rooms from this guide.
- Replaced Rondo seed secured-room data with Rondo Secret Rooms from this guide.
- Upgraded Erangel, Taego, Deston, Vikendi, and Paramo source metadata to this guide where applicable.

### Reddit: HotdropWarrior secret room maps

URL: https://www.reddit.com/r/PUBATTLEGROUNDS/comments/18je495/i_created_some_pubg_secret_room_maps_for_my_clan/

Status: useful community map source, not official.

What it provides:

- Image maps for Erangel, Taego, Vikendi, Deston, Paramo, Karakin, and Sanhok.
- A later updated Taego image after users noticed 3 missing rooms.
- A Discord message link from the author for higher-resolution versions:
  https://discord.com/channels/207018395139309569/986071833025605672/1230567303436042351

Important notes from the thread:

- Taego has 15 secret rooms according to the correction discussion.
- The author says the uploaded maps are 2048x2048 and higher-resolution versions exist on PUBG Discord.
- Erangel rooms are harder to read from Reddit compression; Discord source is preferred.
- Rondo was not covered in the original December 2023 post; the author said Rondo did not have that system yet at the time.

Use in database:

- Mark as `trusted_community_map` with `confidence=medium` only after the image marker can be read clearly.
- Do not mark individual room coordinates as `high` until checked in the current PC live build or in PUBG Bridge replay.

Current blocker:

- Direct `curl` download from `preview.redd.it` returned 403 from the CDN, so the image could not be inspected locally through the CLI.
- If the user can upload the Reddit/Discord images, we can transcribe the map markers into JSON.

### Reddit: all secret rooms/security rooms/bear caves/labs collection

URL: https://www.reddit.com/r/PUBATTLEGROUNDS/comments/1e4aoqd/maps_for_all_secret_rooms_security_rooms_bear/

Status: useful source index, not official.

What it provides:

- Erangel image link.
- Taego secret room source link.
- Taego Error Space map.
- Discussion that Rondo market locations are already marked in-game.
- Recent comments asking for Miramar secret room locations, which suggests Miramar needs extra verification before adding.

Use in database:

- Good source discovery page.
- Treat comments as leads, not verified data.

### Official PUBG Update 26.1

URL: https://pubg.com/en/news/6717

Status: official source.

What it confirms:

- Erangel Secret Rooms were added throughout Erangel.
- They are accessed through underground entrances in natural surroundings.
- They use world-spawned Secret Room Keys.
- They are available in Normal and Custom Matches.

Use in database:

- Requirements and existence: `official_patch_notes`, `confidence=high`.
- Exact coordinates: still need community map/manual verification.

### Official PUBG Update 40.1

URL: https://pubg.com/en/news/9690

Status: official source.

What it confirms:

- All-In-One Repair Kit, Emergency Cover Flare, and Jammer Pack spawn in Secret Rooms as of Update 40.1.
- PUBG Bridge provides browser 2D Replays, useful for manual verification workflow.

Use in database:

- Loot contents: `official_patch_notes`, `confidence=high`.
- Verification workflow: use PUBG Bridge screenshots to confirm room points.

### Official PUBG Update 41.1

URL: https://pubg.com/en/news/9926

Status: official source.

What it confirms:

- Emergency Support Flare can be obtained from Secret Rooms.
- Jammer Pack Lv.3 can be obtained from Secret Rooms.

Use in database:

- Current secret room loot expectation: `official_patch_notes`, `confidence=high`.

### Official PUBG Update 21.2

URL: https://pubg.com/en/news/4552

Status: official source.

What it confirms:

- Vikendi Secret Rooms contain valuable items and are scattered throughout the map.
- Vikendi Secret Rooms use the world-spawned Security Key.
- They are available in Normal and Custom Matches on Vikendi.

Use in database:

- Vikendi requirement/existence: `official_patch_notes`, `confidence=high`.
- Exact room marker callouts still require source map/manual verification.

### Official PUBG Update 40.2

URL: https://pubg.com/en/news/9809?category=patch_notes

Status: official source.

What it confirms:

- Vikendi Secret Rooms had loot-list additions including Jammer Pack, Emergency Pickup, Folded Shield, Mountain Bike, Mortar, All-In-One Repair Kit, Stun Gun, Zipline Gun, and Emergency Cover Flare.

Use in database:

- Vikendi loot expectation: `official_patch_notes`, `confidence=high`.

### Dot Esports: Erangel

URL: https://dotesports.com/pubg/news/how-to-find-the-erangel-secret-basement-key-in-pubg

Status: editorial guide, useful corroboration.

What it states:

- Erangel has 15 Secret Rooms.
- They use Secret Room/Basement Key.
- Wooden entrance must be broken first, then unlocked with the key.
- Keys spawn randomly as global loot.

Use in database:

- Good corroboration for player-facing instructions.
- Still verify exact room locations against current PC live.

### Dot Esports: Taego

URL: https://dotesports.com/pubg/news/all-pubg-taego-secret-room-locations-and-how-to-get-keys

Status: editorial guide, useful corroboration.

What it states:

- Taego has 15 Secret Rooms.
- Requires Secret Room Key.
- Rooms are hidden behind murals in similar blue-roof buildings.
- Keys spawn randomly as ground loot.
- Taego rooms can contain Self-AED and mid/high-tier loot.

Use in database:

- Good source for requirements, count, room appearance, and loot expectation.
- Exact room locations should be read from map image and checked in PC live.

## Next Extraction Tasks

1. Get local copies of high-resolution images from the Reddit post or PUBG Discord.
2. For each image, transcribe markers into `locations` as readable callouts:

```text
map: Taego
room: Taego Secret Room
callout: northwest of Kang Neung compound
grid: optional
source: trusted_community_map
confidence: medium
```

3. Check a sample of each map in PC live/custom or PUBG Bridge before promoting to `confidence=high`.
4. Update `database/*.json` and run:

```bash
python tools/validate_database.py --strict-useful
```

## User-Provided Image Transcription

The user supplied seven Letrix/HotdropWarrior-style map images in chat on 2026-05-31. These images were used as `trusted_community_map` source material with `confidence=medium`.

Integrated into JSON:

- Image 1: Erangel Secret Rooms, 15 readable marker callouts.
- Image 2: Taego Secret Rooms, 15 readable marker callouts.
- Image 3: Vikendi Security Rooms and Bear Caves, readable marker callouts.
- Image 4: Deston Security Rooms and Pillar Trucks, added `database/deston.json`.
- Image 5: Paramo Secret Rooms, added `database/paramo.json`.
- Image 6: Karakin Tunnel Entrances and Jamila Buildings, added `database/karakin.json`.

Not integrated as secret-room data:

- Image 7: Sanhok Bootcamp drop-location image. It is useful tactical context, but it is not a secret-room/security-room map. Keep it for drop-route work instead of mixing it into `/secret`.

Quality caveat:

- The image markers were manually transcribed into human-readable callouts, not exact coordinates.
- Promote individual locations to `confidence=high` only after PC live/custom match or PUBG Bridge verification.
