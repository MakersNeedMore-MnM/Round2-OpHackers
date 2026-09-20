"""ORCA FastAPI entry point."""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from models import HealthResponse
from routers import catalog, optimize, runs

app = FastAPI(title="ORCA backend", version="1.0.0")

# Explicit origin allowlist — never combine allow_credentials=True with "*".
_origins_env = os.environ.get("ORCA_FRONTEND_ORIGIN", "http://localhost:5173")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="online", engine_version="1.0.0", backend=True)


app.include_router(catalog.router)
app.include_router(optimize.router)
app.include_router(runs.router)
