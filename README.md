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
│   │   ├── hybrid_screener.py
│   │   └── screener_output/   # generated timestamped run CSVs (gitignored)
│   ├── data/
│   └── results/
├── frontend/         # Vite + React UI (Discover home)
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
├── Makefile          # Root install / run / build / lint commands
├── .env.example
└── README.md
```

Both apps live at the repository root. No `apps/` wrapper is required.

## Discover

The frontend home page is **Discover**: launch the hybrid pullback screener, browse recent runs, and inspect results before researching individual names.

- **Run Screener** starts a hybrid screener job asynchronously via the backend. Only one run is active at a time; the UI polls until completion, then selects the new result.
- Results load as a table with an **All / Candidates** toggle (full universe vs. names that pass the automated gates).
- **Ticker search** filters the table by ticker (case-insensitive).
- **Run history** lists the last 14 days of completed runs (newest first); pick a prior run to reload its table.

Each run writes a paired, collision-safe CSV set under `backend/screener/screener_output/`:

```text
hybrid_all_results_YYYY-MM-DD_HHMMSS.csv
hybrid_candidates_YYYY-MM-DD_HHMMSS.csv
```

These outputs (and related run metadata) are generated and local-only — gitignored; do not commit them.

The Discover UI talks to `/api/screener/hybrid` on the FastAPI backend. In local development, the Vite proxy forwards those requests to `http://localhost:8000`, so both `make run-backend` and `make run-frontend` must be running.

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

From the repository root (separate terminals):

```bash
make run-backend      # uvicorn backend.main:app on http://0.0.0.0:8000
make run-frontend     # Vite dev server (proxies /api → backend)
```

Equivalent without Make:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm run dev
```

Open the Vite URL shown in the terminal; Discover is the home page.

## Build & lint

```bash
make build            # production frontend build
make lint             # backend compileall + frontend eslint
```

## Notes

- Backend Python dependencies: `backend/requirements.txt`
- Frontend Node dependencies: `frontend/package.json` (React 19, Vite 8, Tailwind CSS 4)
- Frontend Node runtime: recommended Node 24 LTS via `.nvmrc`; `frontend/package.json` `engines` accepts `>=24.18.0`
- Secrets and generated outputs (`client_secret*.json`, `backend/results/`, `backend/screener/screener_output/`, transcript data, legacy screener CSVs, `frontend/dist/`) are gitignored; keep them local.
