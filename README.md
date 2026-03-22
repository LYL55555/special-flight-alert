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
- **Telegram:** Optional digest after each run plus Excel attachments; set `TELEGRAM_EACH_ALERT=1` for one message per emitted alert (noisy). See [Telegram real-time push](#telegram-bot-real-time-push) below.

## Requirements

- **Python 3.10+** (3.11+ recommended; the project has been run on 3.13).
- Network access to Flightradar24 endpoints used by the bundled **FlightRadarAPI** Python client (`python/`).
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

3. **Install dependencies** (editable install of the vendored SDK under `../python`)

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Telegram (optional)**

   ```bash
   cp .env.example .env
   # Edit .env: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
   ```

   Do **not** commit `.env`. Only `.env.example` belongs in git.

### Telegram Bot (real-time push)

The bot does not open a long-lived WebSocket to Flightradar24; “real-time” here means **pushing to your phone as soon as a run finishes**. Each time `main.py` completes a cycle, if `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set, it sends a **digest** (new / expired / current qualifying flights) and attaches the **Excel snapshot** files when applicable. Set `TELEGRAM_EACH_ALERT=1` in the environment if you also want **one Telegram message per emitted alert** (can be very chatty on busy days).

**Getting credentials**

1. In Telegram, talk to [@BotFather](https://t.me/BotFather), create a bot, and copy the **HTTP API token** → this is `TELEGRAM_BOT_TOKEN`.
2. Start a chat with your bot (send any message). To obtain your chat id, you can use the Telegram “getUpdates” API with your token, or message [@userinfobot](https://t.me/userinfobot) — the numeric id you send alerts to is `TELEGRAM_CHAT_ID` (groups use negative ids).

**GitHub Actions (scheduled cloud runs)**

The workflow [`.github/workflows/run.yml`](.github/workflows/run.yml) runs **`python main.py` four times per day** at **00:00, 06:00, 12:00, and 18:00 UTC** (plus manual **Run workflow**). That gives you **periodic push notifications without keeping your laptop on**. Caveats:

- GitHub’s `schedule` uses **UTC** and is **best-effort** (occasional delays).
- Heavy polling can still hit **Flightradar24 / IP throttling**; if you see failures, reduce frequency further or use `--no-details` / shorter horizons in `config.py`.
- Artifact CSV/XLSX from Actions lives only on the runner for that job unless you add an **upload-artifact** step; Telegram is still the main “delivery” channel in this setup.

**Repository secrets (Actions)**

In the GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**, add exactly these **names**:

| Secret name | Value |
|-------------|--------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather |
| `TELEGRAM_CHAT_ID` | Your (or group) chat id |

The workflow passes them into the job as environment variables (see `run.yml`). Optional: add `TELEGRAM_EACH_ALERT` to the `env:` block of the “Run bot” step if you want per-alert messages in CI.

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
- **`python/`** — Upstream **FlightRadarAPI** Python package (same tree as [JeanExtreme002/FlightRadarAPI](https://github.com/JeanExtreme002/FlightRadarAPI)); used via `pip install -r alert_engine/requirements.txt` (`-e ../python`).
- **`nodejs/`** — Upstream **flightradarapi** npm package sources (optional; for Node.js users mirroring the original project).
- **`docs/`**, **`mkdocs.yml`** — Documentation sources for the upstream SDK site.
- **`sample data/`** — **Sample output** for **BOS** (CSV + Excel) from a single schedule run on **2026-03-22** (`python main.py --airports BOS --no-details`); static demo only, not updated live.
- **`LICENSE`** — MIT (original FlightRadarAPI license; see below).

## Acknowledgments

This project builds on **[FlightRadarAPI](https://github.com/JeanExtreme002/FlightRadarAPI)** by Jean Loui Bernard Silva de Jesus — an unofficial Python/Node SDK for Flightradar24 that makes access to airport boards, live flights, and details straightforward. Thank you to the maintainers and contributors of that project. The `LICENSE` file retains the upstream MIT license; the alert engine is offered under the same terms.

If you use Flightradar24 data, respect their [terms and conditions](https://www.flightradar24.com/terms-and-conditions) and consider the [official FR24 API](https://fr24api.flightradar24.com/) for production or commercial workloads.
