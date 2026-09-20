# Round2-OpHackers
Repository for team OpHackers for Round 2
# ORCA — Orbital Rescue and Collision Avoidance

Multi-objective trajectory optimizer for satellite rendezvous/rescue planning.
NSGA-II searches over departure timing, phasing, and thruster impulse split to
find a Pareto front trading off ΔV, time-to-rendezvous, collision risk, and
capture probability — subject to hard constraints (ΔV budget, thruster
impulse caps, Lambert convergence).

## Stack

- **Frontend**: React + TypeScript + Vite, Three.js for the 3D globe/orbit
  view, Recharts for the convergence/Pareto charts.
- **Backend**: FastAPI + pymoo (NSGA-II) + numpy, SGP4 for real catalog
  satellites, live TLE data from Celestrak.
- **Physics**: RK4 + J2-perturbed two-body propagation and a universal-variable
  Lambert solver, implemented independently in Python (`backend/engine/`) and
  TypeScript (`src/simulation/orbitalMechanics.ts`) and kept numerically
  synced via an automated parity check (see below).

## Running locally

Backend:
```bash
cd backend
pip install -r requirements.txt
./run.sh          # or: uvicorn main:app --reload
```

Frontend:
```bash
npm install
npm run dev
```

By default CORS only allows `http://localhost:5173`. To allow a different
frontend origin, set `ORCA_FRONTEND_ORIGIN` (comma-separated for multiple
origins) before starting the backend.

## Health check

```bash
curl http://localhost:8000/health
```
Returns `{"status": "online", "engine_version": "1.0.0", "backend": true}`.
Useful as a liveness probe / smoke test after deploy.

## Tests

Backend (pytest — lambert solver, hard constraints, propagator, NSGA-II smoke
tests):
```bash
cd backend
pytest -q
```

Frontend (vitest — TS orbital mechanics, optimizer helpers, and a physics
parity check against the Python engine):
```bash
npm test
```

Type-check:
```bash
npx tsc --noEmit
```

## CI

`.github/workflows/ci.yml` runs on every push/PR: backend pytest, frontend
vitest + `tsc --noEmit`, and a physics parity check that fails the build if
the Python and TypeScript propagators drift apart (regenerate
`backend/scripts/parity_fixture.json` via
`python backend/scripts/parity_check.py` if a change is intentional).

## Known limitations (by design, for now)

- Run/sweep state (`_LIVE`, `_RUNS` in `backend/routers/optimize.py`) is kept
  in-process — fine for a single uvicorn worker / demo, not for multi-worker
  deployment. Would move to Redis for that.
