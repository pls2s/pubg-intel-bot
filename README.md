# PUBG Intel Bot

Telegram bot for fast PUBG map knowledge lookup: vehicle spawns, secret rooms, loot routes, drop recommendations, and zone prediction.

## Stack

- Python 3.12
- aiogram v3
- Pillow for generated prediction images
- SQLite for query logs
- JSON map database
- Environment variables with `.env`

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `BOT_TOKEN` from BotFather.

```bash
python bot.py
```

## Commands

- `/start` - open the bot
- `/help` - show help
- `/vehicle <location or map>` - vehicle spawn lookup
- `/secret <map>` - secret room lookup
- `/loot <location>` - loot intelligence
- `/drop <map>` - drop recommendations
- `/zone <map/phase/current circle hints>` - phase info and rule-based final-zone prediction

Examples:

```text
/vehicle pochinki
/secret taego
/loot school
/drop erangel
/zone erangel phase 4 school roz
where car pochinki
รถแถว Pochinki อยู่ตรงไหน
Secret room ใน Vikendi อยู่ไหน
ของดีใน School มีอะไร
จุดลงเงียบๆใน Erangel
วง 3 Erangel กลางวง School กิน Rozhok
```

Secret-room and special-location answers send a map image first when that entry has an `image_url` in JSON. If Telegram cannot load the image, the bot falls back to the normal text answer.

## Project Structure

```text
pubg-intel-bot/
├── bot.py
├── config.py
├── database/
│   ├── erangel.json
│   ├── miramar.json
│   ├── sanhok.json
│   ├── vikendi.json
│   ├── taego.json
│   └── rondo.json
├── handlers/
│   ├── zone.py
├── models/
├── services/
├── utils/
├── requirements.txt
├── .env.example
└── README.md
```

## Data Format

Each JSON file is one PUBG map:

```json
{
  "map": "Erangel",
  "aliases": ["erangel", "เอรันเกล"],
  "locations": [
    {
      "name": "Pochinki",
      "aliases": ["โพชินกิ"],
      "vehicles": [
        {
          "name": "North Road",
          "description": "Check both sides of the main road.",
          "landmarks": ["north compound"]
        }
      ],
      "loot": {
        "quality": "high",
        "high_tier_buildings": ["central two-story houses"],
        "route": ["land central roofs", "clear west garage"],
        "notes": "Popular hot drop."
      },
      "danger": "high",
      "description": "Popular hot drop area"
    }
  ],
  "secret_rooms": [],
  "drops": {
    "hot": ["Pochinki"],
    "medium": ["Rozhok"],
    "safe": ["Farm compounds"]
  }
}
```

The loader also supports the compact single-location example from the prompt by wrapping it into a map file automatically.

## Search Behavior

`SearchService` is keyword-first:

- English and Thai intent keywords identify `vehicle`, `secret`, `loot`, and `drop`.
- Zone keywords identify `zone` / `circle` / `phase` / `วง` / `ทำนายวง`.
- `MapService` performs fuzzy matching with aliases, token overlap, and spelling-tolerant similarity.
- Natural-language messages are handled by `handlers/search.py`.

This keeps the bot deterministic now while leaving a clean place to add AI/NLU later.

## Zone Prediction

`/zone` is a rule-based assistant that sends a generated prediction image plus detailed Thai text. It does not know the server's next circle, but it can estimate likely endgame areas from:

- map name
- current phase
- landmarks mentioned by the player
- direction hints such as north/south/center/edge/water

Examples:

```text
/zone phase 5
/zone erangel phase 4 school roz
วง 3 Erangel กลางวง School กิน Rozhok
```

The current image is a schematic heatmap. The next upgrade path is replacing the schematic background with real map assets and drawing the same candidate areas as overlays.

## SQLite

The bot creates `data/pubg_intel.sqlite3` automatically and logs queries into `user_queries`.

It also stores Telegram image `file_id` values in `image_cache`. The first image send uses the configured URL, then later sends reuse Telegram's cached file ID for faster responses.

Map knowledge stays in JSON. SQLite is intentionally used only for persistence/analytics so the knowledge base remains easy to edit and review.

## Data Quality

This project now tracks source quality with optional `verification` blocks on maps, locations, vehicle spawns, loot profiles, secret rooms, and drop recommendations.

Default validation checks that the JSON database can be loaded by the bot:

```bash
python tools/validate_database.py
```

Strict Useful-level validation enforces per-entry verification metadata:

```bash
python tools/validate_database.py --strict-useful
```

See [docs/pubg-pc-useful-data-plan.md](docs/pubg-pc-useful-data-plan.md) for the PUBG: BATTLEGROUNDS PC data collection checklist and source policy.

## Notes

The included JSON files are sample production-shaped data. PUBG map rules and secret room mechanics can change by patch, so keep the `database/*.json` files updated with your target PUBG version.
