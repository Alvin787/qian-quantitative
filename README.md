# qian-quantitative

Platform for automated technical analysis and discovery of securities for swing trading.

## Layout

```text
qian-quantitative/
├── backend/          # FastAPI app, ai, screener, diary, watchlists, positions, generated data/results
│   ├── main.py
│   ├── requirements.txt
│   ├── ai/
│   ├── screener/
│   │   ├── finviz.py
│   │   ├── screens.py
│   │   ├── hybrid_screener.py
│   │   ├── strategies/
│   │   │   ├── base.py
│   │   │   ├── reversal.py
│   │   │   └── breakout.py
│   │   └── screener_output/   # generated timestamped run CSVs (gitignored)
│   ├── diary/                 # Market Diary snapshot + persistence APIs
│   │   └── diary_data/        # local narrative/watchlists JSON (gitignored)
│   ├── watchlists/            # Watchlists funnel APIs
│   │   └── watchlist_data/    # local funnel JSON (gitignored)
│   ├── positions/             # Position sizing + day-indexed management calculator APIs
│   ├── data/
│   └── results/
├── frontend/         # Vite + React UI (Screener home)
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       └── components/
│           └── watchlists-panel.tsx
├── Makefile          # Root install / run / build / lint commands
├── .env.example
└── README.md
```

Both apps live at the repository root. No `apps/` wrapper is required.

## Market Diary

Pre-open situational awareness for the 30–60 minutes before the US session. Open the sidebar **Market Diary** tab. **Refresh** rebuilds the machine snapshot; narrative **Save** persists JSON locally on the backend host under `backend/diary/diary_data/` (gitignored). Focus / Stalk on the page are read-only from the Watchlists funnel. `PUT /api/diary/watchlists` still exists for themes/leadership (and unused focus/stalk JSON).

Sections on the page: narrative, read-only Focus / Stalk from the Watchlists funnel, short-term breadth (`$MMTW`, Finviz NH/NL proxy, `$NYHL`/`$NAHL`), market level, sub-market, sectoral, themes/leadership, and CNBC 5 Things.

| Source | What it feeds |
| --- | --- |
| `yfinance` | Index / style / sector ETF metrics and watchlist enrichment |
| Barchart scrape | `$MMTW` quote + 5-day history; `$NYHL` / `$NAHL` nets |
| Finviz NH-NL proxy | New-high / new-low totals (Finviz universe, not exchange official) |
| CNBC scrape | Latest “5 Things” title, link, and short excerpt |
| Manual | Narrative text; themes / leadership lists |

**Limitations:** Finviz NH/NL is not official exchange new highs/lows; `$MMTW` is an unofficial Barchart scrape that can break; there is no paid Barchart OnDemand integration.

Diary APIs live under `/api/diary` on the FastAPI backend. With both `make run-backend` and `make run-frontend` running, the Vite proxy forwards those requests like the Screener.

## Position Management

Educational risk and trade-management calculator for open (or hypothetical) longs. Open the sidebar **Positions** tab. The page has two stacked sections, in this order: (1) **Position sizing / risk**, (2) **Position management**.

| API | Role |
| --- | --- |
| `POST /api/positions/size` | Share count + initial 3-stop book from equity, entry, and final stop |
| `POST /api/positions/plan` | Day-indexed action plan / stop book / nuance alerts for an open trade |

Session dates (`entry_date`, `as_of_date`, and related close-below dates) are US equity calendar days in IANA timezone `America/New_York` (`YYYY-MM-DD`, not UTC instants). **Day index** counts XNYS trading sessions from entry as day 0 via `exchange-calendars` (skipping weekends and exchange holidays).

Sizing defaults follow the master trading strategy: **0.5%–1.0%** of equity risk (`fixed_pct`), with optional **Kelly / half-Kelly** (still clamped to a max risk %).

**Limitations:** ATR / MA / ORL and similar levels are manual inputs (no live market-data fetch); open trades are not persisted on the backend; this is an educational calculator, not broker or order execution.

Positions APIs live under `/api/positions` on the FastAPI backend. With both `make run-backend` and `make run-frontend` running, the Vite proxy forwards those requests like the Screener and Market Diary.

## Screener

The sidebar **Screener** tab is the home page. Use the strategy dropdown to pick **Breakout** (first) or **Reversal** (second). A run scans only the Finviz screens that strategy declares. Only one run is active at a time across all strategies; the UI polls until completion, then selects the new result.

- **Reversal** is the hybrid pullback strategy: **All / Candidates** toggle, unchanged automated gates, ticker search, and the last 14 days of run history.
- **Breakout** is a fail-closed post-close union of independent screen families. Rows expose `ticker`, `industry`, `screen_count`, `screen_family_count`, `source_screens`, and `as_of_session`.
- The results table paginates at **100 rows per page** (page indicator and previous/next).

### Screens

All 14 Finviz screens live in `backend/screener/screens.py`. Strategies reference screens by id; adding a screen to a strategy is a one-line change to its `screen_ids`.

Each run writes collision-safe CSVs under `backend/screener/screener_output/`:

```text
hybrid_all_results_YYYY-MM-DD_HHMMSS.csv     # Reversal, all
hybrid_candidates_YYYY-MM-DD_HHMMSS.csv      # Reversal, candidates
breakout_all_results_YYYY-MM-DD_HHMMSS.csv   # Breakout, all
```

These outputs (and related run metadata JSON) are generated and local-only — gitignored; do not commit them.

The Screener UI talks to `/api/screener/strategies` and `/api/screener/{strategy}/runs...` on the FastAPI backend. In local development, the Vite proxy forwards those requests to `http://localhost:8000`, so both `make run-backend` and `make run-frontend` must be running.

## Watchlists

The sidebar **Watchlists** tab is the name funnel: **Master → Stalk → Focus → Back**. Post-close **Review** ranks a chart-review queue from Breakout output; there is no auto-promote. The strongest automated label is `chart_review_ready`, which is not Focus; Focus is a manual move after the chart pass. Watchlists earnings leeway uses XNYS sessions. **Copy** buttons produce comma-separated tickers for TradingView. Data lives under `backend/watchlists/watchlist_data/` (gitignored).

## Setup

1. Copy environment template and fill in values (names only in the example):

   ```bash
   cp .env.example .env
   ```

2. Create a Python virtualenv (recommended) and install dependencies from the repo root:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   make install
   ```

   Or install each app separately:

   ```bash
   make install-backend
   make install-frontend
   ```

## Run

From the repository root, one terminal:

```bash
make run              # backend + frontend together (Ctrl+C stops both)
```

Or run them separately:

```bash
make run-backend      # uvicorn backend.main:app on http://127.0.0.1:8000
make run-frontend     # Vite dev server (proxies /api → backend)
```

Open the Vite URL shown in the terminal; Screener is the home page. Watchlist mutation APIs are unauthenticated and the server must stay on loopback.

## Build & lint

```bash
make build            # production frontend build
make lint             # backend compileall + frontend eslint
make test-backend     # backend pytest suite
```

## Notes

- Backend Python dependencies: `backend/requirements.txt`
- Frontend Node dependencies: `frontend/package.json` (React 19, Vite 8, Tailwind CSS 4)
- Frontend Node runtime: recommended Node 24 LTS via `.nvmrc`; `frontend/package.json` `engines` accepts `>=24.18.0`
- Secrets and generated outputs (`client_secret*.json`, `backend/results/`, `backend/screener/screener_output/`, `backend/diary/diary_data/`, `backend/watchlists/watchlist_data/`, transcript data, legacy screener CSVs, `frontend/dist/`) are gitignored; keep them local.
