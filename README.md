# qian-quantitative

Platform for automated technical analysis and discovery of securities for swing trading.

## Layout

```text
qian-quantitative/
├── backend/          # FastAPI app, utils, screener, generated data/results
│   ├── main.py
│   ├── requirements.txt
│   ├── utils/
│   ├── screener/
│   │   ├── finviz.py
│   │   ├── screens.py
│   │   ├── hybrid_screener.py
│   │   ├── strategies/
│   │   │   ├── base.py
│   │   │   ├── reversal.py
│   │   │   └── breakout.py
│   │   └── screener_output/   # generated timestamped run CSVs (gitignored)
│   ├── data/
│   └── results/
├── frontend/         # Vite + React UI (Screener home)
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
├── Makefile          # Root install / run / build / lint commands
├── .env.example
└── README.md
```

Both apps live at the repository root. No `apps/` wrapper is required.

## Screener

The sidebar **Screener** tab is the home page. Use the strategy dropdown to pick **Breakout** (first) or **Reversal** (second). A run scans only the Finviz screens that strategy declares. Only one run is active at a time across all strategies; the UI polls until completion, then selects the new result.

- **Reversal** is the hybrid pullback strategy: **All / Candidates** toggle, unchanged automated gates, ticker search, and the last 14 days of run history.
- **Breakout** is currently a universe-only union of 12 screens. Rows expose `ticker`, `industry`, `screen_count`, and `source_screens`; there are no scoring criteria yet.
- The results table paginates at **100 rows per page** (page indicator and previous/next).

### Screens

All 13 Finviz screens live in `backend/screener/screens.py`. Strategies reference screens by id; adding a screen to a strategy is a one-line change to its `screen_ids`.

Each run writes collision-safe CSVs under `backend/screener/screener_output/`:

```text
hybrid_all_results_YYYY-MM-DD_HHMMSS.csv     # Reversal, all
hybrid_candidates_YYYY-MM-DD_HHMMSS.csv      # Reversal, candidates
breakout_all_results_YYYY-MM-DD_HHMMSS.csv   # Breakout, all
```

These outputs (and related run metadata JSON) are generated and local-only — gitignored; do not commit them.

The Screener UI talks to `/api/screener/strategies` and `/api/screener/{strategy}/runs...` on the FastAPI backend. In local development, the Vite proxy forwards those requests to `http://localhost:8000`, so both `make run-backend` and `make run-frontend` must be running.

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
make run-backend      # uvicorn backend.main:app on http://0.0.0.0:8000
make run-frontend     # Vite dev server (proxies /api → backend)
```

Open the Vite URL shown in the terminal; Screener is the home page.

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
- Secrets and generated outputs (`client_secret*.json`, `backend/results/`, `backend/screener/screener_output/`, transcript data, legacy screener CSVs, `frontend/dist/`) are gitignored; keep them local.
