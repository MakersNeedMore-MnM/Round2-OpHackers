"""
Pydantic v2 schemas for ORCA — mirror the frontend `src/types.ts` field-for-field.
Units are carried in field names (`deltaVKmS`, `etaHrs`, `altKm`, ...).
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict
from sqlmodel import SQLModel, Field as SQLField


# ─── Units discipline ────────────────────────────────────────────────────────
# ΔV is ALWAYS a vector magnitude |v_transfer - v_current| in km/s and is >= 0.
# ETA is ALWAYS a Lambert time-of-flight in hours and is >= 0.
# Fuel is ALWAYS a 0..100 percentage of tank capacity, mechanically tied to ΔV.


class Vec3(BaseModel):
    x: float
    y: float
    z: float


class OrbitalState(BaseModel):
    position: Vec3
    velocity: Vec3
    a: float = 0.0
    e: float = 0.0
    i: float = 0.0
    raan: float = 0.0
    argPeriapsis: float = 0.0
    trueAnomaly: float = 0.0
    period: float = 0.0


class ObjectiveValues(BaseModel):
    """All four competing objectives for one candidate.

    deltaV/etaHrs are physical magnitudes: finite and non-negative.
    collisionRisk/captureProbability are probabilities in 0..1.
    """
    model_config = ConfigDict(populate_by_name=True)

    deltaV: float = Field(alias="deltaVKmS")  # km/s, >= 0
    timeToRendezvous: float = Field(alias="etaHrs")  # hours, >= 0
    collisionRisk: float        # 0..1
    captureProbability: float   # 0..1


class TrajectoryPoint(BaseModel):
    time: float
    position: Vec3
    velocity: Vec3


class CandidateTrajectory(BaseModel):
    id: str
    objectives: ObjectiveValues
    waypoints: List[TrajectoryPoint]
    transferOrbit: OrbitalState
    rank: int
    dominated: bool
    violatesConstraint: bool
    impulse1: float = 0.0
    impulse2: float = 0.0
    propellantUsedFraction: float = 0.0
    lambertConverged: bool = True
    closestApproachKm: float = float("inf")
    closestApproachAtSec: float = 0.0
    feasible: bool = True


class ParetoPoint(BaseModel):
    id: str
    deltaV: float
    timeToRendezvous: float
    collisionRisk: float
    captureProbability: float
    trajectory: CandidateTrajectory
    violatesConstraint: bool = False


# ─── Request / response models ───────────────────────────────────────────────


class ThrusterClass(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Constraints(BaseModel):
    deltaVBudgetKmS: float
    thrusterClass: ThrusterClass = ThrusterClass.medium
    tumbleRateDegS: float = 2.0
    debrisDensity: float = 0.3
    commsWindowSec: float = 15 * 60.0


class Weights(BaseModel):
    fuel: float = 0.25
    time: float = 0.25
    risk: float = 0.25
    capture: float = 0.25


class OrbitalElements(BaseModel):
    altKm: float
    inclDeg: float
    raanDeg: float = 0.0
    ecc: float = 0.001
    argPeriapsisDeg: float = 0.0
    trueAnomalyDeg: float = 0.0


class TargetSpec(BaseModel):
    line1: Optional[str] = None
    line2: Optional[str] = None
    orbitalElements: Optional[OrbitalElements] = None


class StateVec(BaseModel):
    """Pre-resolved ECI state (km / km/s). Preferred when the client already has them."""
    position: Vec3
    velocity: Vec3


class OptimizeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target: TargetSpec
    interceptorOrigin: OrbitalElements
    weights: Weights = Weights()
    constraints: Constraints
    population: int = 40
    generations: int = 30
    seed: Optional[int] = None
    targetState: Optional[StateVec] = None
    interceptorState: Optional[StateVec] = None
    scenarioLabel: str = "scenario"
    real_vs_simulated: Optional["RealVsSimulated"] = None


class RealVsSimulated(BaseModel):
    orbits: str = "real SGP4/J2"
    distressEvent: str = "simulated"


class RunCreated(BaseModel):
    runId: str
    websocketUrl: str
    real_vs_simulated: RealVsSimulated


class GenBest(BaseModel):
    deltaV: float
    time: float
    risk: float
    capture: float


class GenMean(BaseModel):
    deltaV: float
    time: float
    risk: float
    capture: float


class GenerationPayload(BaseModel):
    """One streamed message per generation, then a final full-front message."""
    generation: int
    best: GenBest
    mean: GenMean
    paretoFront: List[ParetoPoint]
    final: bool = False
    runId: str
    real_vs_simulated: RealVsSimulated = RealVsSimulated()


class SweepRequest(BaseModel):
    parameter: str = Field(..., pattern="^(fuelBudget|tumble|debris)$")
    values: List[float]
    baseRequest: OptimizeRequest


class SweepCreated(BaseModel):
    sweepId: str
    websocketUrl: str
    real_vs_simulated: RealVsSimulated


# ─── Catalog ─────────────────────────────────────────────────────────────────


class OrbitClass(str, Enum):
    LEO = "LEO"
    MEO = "MEO"
    GEO = "GEO"
    HEO = "HEO"


class CatalogSatellite(BaseModel):
    noradId: str
    name: str
    line1: str
    line2: str
    altKm: float
    inclDeg: float
    periodMin: float
    epoch: str
    orbitClass: OrbitClass
    position: Optional[Vec3] = None
    velocity: Optional[Vec3] = None
    real_vs_simulated: Optional[RealVsSimulated] = None


class HealthResponse(BaseModel):
    status: str
    engine_version: str = "1.0.0"
    backend: bool = True


# ─── Persistence (SQLite via SQLModel) ───────────────────────────────────────


class RunRecord(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    runId: str = SQLField(index=True, unique=True)
    scenarioLabel: str
    pinned: bool = SQLField(default=False, index=True)
    createdAt: str
    payloadJson: str


# Resolve forward refs
OptimizeRequest.model_rebuild()
RealVsSimulated.model_rebuild()
