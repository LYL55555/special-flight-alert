# Special Flight Alert

Scan airports for **special liveries**, **rare aircraft types**, and other noteworthy flights using [Flightradar24](https://www.flightradar24.com/) schedule data (via the community [FlightRadarAPI](https://github.com/JeanExtreme002/FlightRadarAPI) SDK).

This repo is designed as a **local-first** project: run the API and web UI on your Mac (or PC), use your home network IP to reach FR24, and keep secrets out of git.

**中文说明** → [README.zh-CN.md](README.zh-CN.md)

> **Disclaimer:** Personal and educational use only. Respect Flightradar24 [terms and conditions](https://www.flightradar24.com/terms-and-conditions). For commercial use, see the [official FR24 API](https://fr24api.flightradar24.com/).

---

## What you get

| Component | Description |
|-----------|-------------|
| **Web UI** (`web/`) | Search by airport code (PVD, JFK, LAX, …), filter results, bilingual EN/zh |
| **HTTP API** (`api/`) | FastAPI service: `GET /api/scan?airport=PVD` |
| **Alert engine** (`alert_engine/`) | CLI daemon: score flights, CSV/Excel output, optional Telegram |
| **MCP server** (`mcp_server/`) | Cursor integration — ask the agent to scan an airport |

---

## Quick start (web demo)

**Requirements:** Python 3.10+

```bash
git clone https://github.com/LYL55555/special-flight-alert.git
cd special-flight-alert

# Install dependencies (from repo root — not alert_engine/)
pip install -r requirements.txt

# Optional: MCP support for Cursor
pip install -r mcp_server/requirements.txt

# One command: API :8000 + web UI :8080
./scripts/run_demo.sh
```

Open **http://127.0.0.1:8080** and search **PVD**, **JFK**, or **LAX**.

Press `Ctrl+C` to stop.

### Port already in use?

```bash
./scripts/stop_demo.sh   # frees 8000 / 8080, stops Docker stack if any
./scripts/run_demo.sh
```

### API only (no web UI)

```bash
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/ | API info |
| http://127.0.0.1:8000/health | Health check |
| http://127.0.0.1:8000/docs | Swagger UI |
| http://127.0.0.1:8000/api/scan?airport=PVD | Scan airport |

---

## Configuration

### Web → API address

Default is in `web/config.js`:

```javascript
window.APP_CONFIG = {
  apiBaseUrl: "http://127.0.0.1:8000",
};
```

If the API runs on another port, copy the example override:

```bash
cp web/config.local.js.example web/config.local.js
# edit apiBaseUrl — config.local.js is gitignored
```

### Secrets (Telegram, etc.)

**Never commit real tokens.** Use a local `.env` file only:

```bash
cp alert_engine/.env.example alert_engine/.env
# Edit alert_engine/.env — TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

`.env` is listed in `.gitignore`. Only `.env.example` (empty placeholders) belongs in git.

For GitHub Actions scheduled runs, put the same names in **Repository Secrets** — not in source code.

---

## Cursor MCP

1. Install deps: `pip install -r mcp_server/requirements.txt` and `pip install -r requirements.txt`
2. Cursor loads `.cursor/mcp.json` automatically
3. In chat: *“Scan PVD for special flights using MCP”*

Tools: `scan_airport`, `health_check`

---

## Alert engine (CLI)

For background monitoring, CSV alerts, Excel snapshots, and optional Telegram digests:

```bash
cd alert_engine
python main.py --airports PVD          # one-shot schedule scan
python main.py --live --airports BOS   # live radius mode
python main.py --loop --poll-seconds 14400
python main.py --help
```

Tune airports, scores, and horizons in `alert_engine/config.py`.  
Special liveries database: `alert_engine/db/special_liveries.csv`.

---

## API behavior notes

- Successful scans return flight JSON with `count`, `flights`, etc.
- If Flightradar24 is unreachable, `/api/scan` returns **HTTP 200** with `status: "degraded"` (not 502) so the UI stays usable.
- Works best on a **residential network**. Datacenter hosts (Render, GitHub Actions runners) are often blocked by FR24/Cloudflare — that is why this project defaults to **local** execution.

---

## Project layout

```
special-flight-alert/
├── api/                 # FastAPI HTTP API
├── alert_engine/        # CLI alert bot + scoring engine
├── web/                 # Static frontend
├── python/              # Vendored FlightRadarAPI SDK
├── mcp_server/          # Cursor MCP
├── scripts/
│   ├── install_deps.sh  # pip install helper
│   ├── run_demo.sh      # local API + web UI
│   └── stop_demo.sh     # free ports 8000/8080
├── requirements.txt     # install from repo root
└── tests/
```

---

## Development

```bash
pip install -r requirements.txt
python3 -m pytest tests/test_api_routes.py -q
```

---

## Acknowledgments

Built on **[FlightRadarAPI](https://github.com/JeanExtreme002/FlightRadarAPI)** (MIT). See `LICENSE`.
