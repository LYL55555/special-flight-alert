# Special Flight Alert

A small Python tool that periodically scans [Flightradar24](https://www.flightradar24.com/) (via the community **FlightRadarAPI** client) for **scheduled boards** or **live traffic** near airports you choose. It scores flights for **rare aircraft types**, **special liveries** (from your CSV database), **military-style operators**, and **diversions**, then writes **per-airport CSV alerts**, maintains **Excel snapshots** for diffing, and can send a **Telegram digest** (and optional per-alert messages).

> **Disclaimer:** For personal or educational use only. Flightradar24’s data and terms apply; for commercial access see [FR24 business contact](https://www.flightradar24.com/) and [terms and conditions](https://www.flightradar24.com/terms-and-conditions). The official API is at [fr24api.flightradar24.com](https://fr24api.flightradar24.com/).

## What it does

- **Schedule mode (default):** Reads each airport’s arrival/departure board for the next *N* hours (`schedule_24h`), scores every row, and emits alerts when the total score ≥ threshold.
- **Live mode (`--live`):** Fetches aircraft inside a **radius** (meters) around each airport center, with optional filtering (`airport_linked`, `arrival`, `departure`, or `all`).
- **Outputs:**
  - Default layout: `alert_engine/alert data/{AIRPORT}/alerts_{AIRPORT}_{timestamp}.csv` and snapshot workbooks (`snapshot_*_latest.xlsx` / per-run copies).
  - Legacy single-file CSV: pass `--output path.csv` (disables the per-airport folder layout).
- **Deduping:** Avoids re-alerting the same aircraft/reason fingerprint for a configurable TTL.
- **Telegram:** Optional digest after each run plus Excel attachments; set `TELEGRAM_EACH_ALERT=1` for one message per emitted alert (noisy).

## Requirements

- **Python 3.10+** (3.11+ recommended; the project has been run on 3.13).
- Network access to Flightradar24 endpoints used by [FlightRadarAPI](https://pypi.org/project/FlightRadarAPI/).
- Optional: a **Telegram bot** token and chat ID for notifications.

## Setup

1. **Clone this repository**

   ```bash
   git clone https://github.com/LYL55555/special-flight-alert.git
   cd special-flight-alert
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   cd alert_engine
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Telegram (optional)**

   ```bash
   cp .env.example .env
   # Edit .env: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
   ```

   Do **not** commit `.env`. Only `.env.example` belongs in git.

5. **Special liveries database**

   By default the engine loads `db/special_liveries.csv` under `alert_engine/`. Edit registrations and metadata to match the liveries you want to detect.

## How to run

From the `alert_engine` directory:

```bash
# One shot: next 24h schedule boards (default airports in config.py)
python main.py

# Live traffic in radius around airports
python main.py --live

# Loop forever (sleep between cycles from config or --poll-seconds)
python main.py --loop --poll-seconds 14400

# Only certain airports (overrides config list)
python main.py --airports BOS,PVD

# Longer schedule horizon (hours)
python main.py --hours 48

# Legacy single CSV output path
python main.py --output ~/rare_alerts.csv
```

CLI flags are documented in `main.py` (`python main.py --help`).

## Tuning parameters

Most behavior is controlled in **`alert_engine/config.py`** (`EngineConfig`). Common knobs:

| Setting | Effect |
|--------|--------|
| `airports` | Tuple of IATA/ICAO codes scanned each cycle. |
| `scan_mode` | `"schedule_24h"` (default) or `"live"` (also toggled via `--live`). |
| `schedule_horizon_hours` | How far ahead to read boards in schedule mode; overridden by `--hours`. |
| `schedule_max_pages` | Cap on paginated schedule fetches per airport (trade-off: coverage vs. time/API load). |
| `radius_meters` | Used **only** in live mode. |
| `movement_filter` | `all` / `airport_linked` / `arrival` / `departure` for live fetches. |
| `alert_min_score` | Minimum **total** score to qualify for an alert. |
| `score_rare_type` / `score_special_livery` / `score_military` | Points per matched rule. |
| `rare_aircraft_codes` | ICAO type codes treated as rare (e.g. widebodies, outsized military). |
| `military_operator_icao` | Operator ICAO prefixes counted as military-style. |
| `dedupe_ttl_seconds` | Suppress repeat alerts for the same fingerprint. |
| `poll_interval_seconds` | Default sleep between `--loop` iterations; override with `--poll-seconds`. |
| `night_penalty` / `night_hours` | Subtract points during a local-time window (e.g. reduce overnight noise). |
| `fetch_details_on_alert` | Call FR24 flight details for qualifying flights (richer ETA/ETD when available). |
| `alerts_csv_path` | Legacy default path when using `--output`; otherwise per-airport files under `alert data/`. |

**CLI overrides:** `--airports`, `--hours`, `--movement`, `--output`, `--no-details`, `--poll-seconds`, `--live`, `--live-details`, `--livery-csv`, `--snapshot-xlsx`.

**Operational notes:**

- FR24 may rate-limit or return sparse fields without a suitable data plan; `--no-details` and shorter horizons reduce calls.
- `--live-details` enables per-aircraft detail fetches in live mode (slower; may require paid access).

## Repository layout (what we ship)

- **`alert_engine/`** — Application code, `db/special_liveries.csv`, `requirements.txt`, `.env.example`, helper `scripts/`.
- **`LICENSE`** — MIT (original FlightRadarAPI license; see below).

Vendored copies of the full **python/** and **nodejs/** SDK trees are **not** included in this repository; install the client from PyPI as declared in `requirements.txt`.

## Acknowledgments

This project builds on **[FlightRadarAPI](https://github.com/JeanExtreme002/FlightRadarAPI)** by Jean Loui Bernard Silva de Jesus — an unofficial Python/Node SDK for Flightradar24 that makes access to airport boards, live flights, and details straightforward. Thank you to the maintainers and contributors of that project. The `LICENSE` file retains the upstream MIT license; the alert engine is offered under the same terms.

If you use Flightradar24 data, respect their [terms and conditions](https://www.flightradar24.com/terms-and-conditions) and consider the [official FR24 API](https://fr24api.flightradar24.com/) for production or commercial workloads.
