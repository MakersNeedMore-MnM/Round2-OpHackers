# ORCA backend

Optional Python service that gives ORCA real orbital data, server-side
NSGA-II optimization, and run persistence. **The frontend runs fully without
it** — if `VITE_ORCA_BACKEND_URL` is unset or `/health` fails, the app
silently uses its client-only engine. Demo safety is non-negotiable.

## Stack
- **FastAPI** + **uvicorn** — async API + WebSocket streaming
- **pymoo** — NSGA-II (non-dominated sort, crowding distance, SBX, polynomial
  mutation, elitist survival)
- **numpy** — RK4/J2 propagation + Monte Carlo uncertainty (numerically
  identical to the frontend so backend-on/off numbers match)
- **sgp4** (python-sgp4) — TLE propagation for the Catalog
- **poliastro** + **astropy** — optional ground-truth validation (not on the
  hot path; server runs without them)
- **SQLModel/SQLite** — zero-setup file persistence for "pin this run"
- **httpx** — Celestrak TLE fetch with on-disk caching

## Run
```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run.sh          # uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Environment
| Variable | Default | Effect |
|---|---|---|
| `VITE_ORCA_BACKEND_URL` *(frontend)* | unset | Base URL of this service. Unset → client-only mode. |
| `ORCA_HOST` / `ORCA_PORT` | `0.0.0.0` / `8000` | Bind address for `run.sh` |
| `ORCA_DB_URL` | `sqlite:///orca_runs.db` | SQLite path |

## API contract
- `GET /health` → `{ status, engine_version, backend }`
- `GET /catalog/satellites?group=…&limit=…` → `CatalogSatellite[]` (SGP4 positions, cached, seed-CSV fallback)
- `GET /catalog/satellites/{noradId}` → full detail + live position
- `POST /optimize/run` → `{ runId, websocketUrl }`
- `WS /optimize/stream/{runId}` → per-generation `{ generation, best, mean, paretoFront, final }`
- `POST /optimize/sweep` → `{ sweepId, websocketUrl }`  ·  `WS /optimize/sweep/{sweepId}`
- `GET /runs`, `GET /runs/{id}`, `POST /runs/{id}/pin`, `GET /runs/pinned`

## Correctness guarantees
- **One propagation path** — waypoints and objective scoring both come from
  `engine/propagation.propagate()`. Catalog uses SGP4 separately.
- **ΔV** is `|v_transfer − v_current|`, a vector magnitude, always ≥ 0, km/s.
- **ETA** is the Lambert time-of-flight, always ≥ 0.
- **Fuel Remaining** is `(current / capacity) × 100`, clamped 0–100, tied to ΔV
  via the rocket equation.
- **Hard constraints filter** — over-budget / over-thruster-cap candidates
  are flagged `feasible:false` and excluded from the Pareto set.
- **Elitism** — pymoo's NSGA-II survival guarantees per-generation best is
  monotonically non-worsening.
- Every response carries a `real_vs_simulated: { orbits, distressEvent }`
  disclosure block.

## Demo-safe fallback
Catalog: live fetch → on-disk cache → bundled `data/seed_satellites.csv`.
Optimizer: if the backend is unreachable, the frontend never blocks — it uses
the client engine. Refresh the seed CSV TLE lines from Celestrak before
judging for fresh epochs:
`https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle`
