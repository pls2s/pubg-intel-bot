# PUBG Intel Bot

Telegram bot for fast PUBG map knowledge lookup: vehicle spawns, secret rooms, loot routes, and drop recommendations.

## Stack

- Python 3.12
- aiogram v3
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

Examples:

```text
/vehicle pochinki
/secret taego
/loot school
/drop erangel
where car pochinki
รถแถว Pochinki อยู่ตรงไหน
Secret room ใน Vikendi อยู่ไหน
ของดีใน School มีอะไร
จุดลงเงียบๆใน Erangel
```

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
- `MapService` performs fuzzy matching with aliases, token overlap, and spelling-tolerant similarity.
- Natural-language messages are handled by `handlers/search.py`.

This keeps the bot deterministic now while leaving a clean place to add AI/NLU later.

## SQLite

The bot creates `data/pubg_intel.sqlite3` automatically and logs queries into `user_queries`.

Map knowledge stays in JSON. SQLite is intentionally used only for persistence/analytics so the knowledge base remains easy to edit and review.

## Notes

The included JSON files are sample production-shaped data. PUBG map rules and secret room mechanics can change by patch, so keep the `database/*.json` files updated with your target PUBG version.
