"""Marine Pollution AI Hackathon - FastAPI backend.

Lightweight: fastapi, uvicorn, numpy, shapely, requests only.
Torch is NEVER imported at module level; real models are imported
lazily inside endpoint handlers, and only when USE_MOCK != "true".
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
MOCK_DIR = BASE_DIR / "mock_data"
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"

app = FastAPI(title="Marine Pollution AI API", version="0.1.0")

# ---- CORS (open for hackathon demo; tighten origins in production) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_mock(name: str) -> dict:
    """Load a mock JSON file from backend/mock_data/."""
    path = MOCK_DIR / name
    if not path.exists():
        raise HTTPException(status_code=500, detail=f"mock file missing: {name}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------- request schemas -------------------------

class DetectionRequest(BaseModel):
    region: dict | None = None            # {"bbox": [min_lon, min_lat, max_lon, max_lat]}
    image_ref: str | None = None          # path/URL to satellite or drone imagery
    threshold: float = 0.5
    timestamp: str | None = None


class DriftRequest(BaseModel):
    source: list[float]                  # [lon, lat] of spill/debris origin
    hours: int = 24                      # forecast horizon
    wind_speed_ms: float | None = None
    wind_direction_deg: float | None = None
    current_speed_ms: float | None = None
    current_direction_deg: float | None = None


class ReportRequest(BaseModel):
    pollution_type: str                  # oil | debris | algal
    location: list[float]                # [lon, lat]
    description: str | None = None
    severity: str = "medium"             # low | medium | high
    reported_by: str | None = None


# ------------------------- endpoints -------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "use_mock": USE_MOCK, "time": datetime.now(timezone.utc).isoformat()}


@app.get("/api/scenario")
def scenario():
    """Current marine-pollution scenario overview for the monitored zone."""
    if USE_MOCK:
        return _load_mock("scenario.json")
    # Real path: aggregate latest detections/forecasts into a scenario summary.
    raise HTTPException(status_code=501, detail="real scenario aggregation not implemented yet")


@app.post("/api/detect/oil")
def detect_oil(req: DetectionRequest):
    """Detect oil slicks in a region or image."""
    if USE_MOCK:
        mock = _load_mock("scenario.json")
        return {
            "task_id": str(uuid.uuid4()),
            "type": "oil",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mock": True,
            "detections": mock.get("oil_detections", []),
        }
    from models.oil.inference import run  # lazy import; heavy deps live here
    try:
        return run(payload=req.model_dump())
    except TypeError:
        return run(req.model_dump())


@app.post("/api/detect/debris")
def detect_debris(req: DetectionRequest):
    """Detect floating marine debris."""
    if USE_MOCK:
        mock = _load_mock("scenario.json")
        return {
            "task_id": str(uuid.uuid4()),
            "type": "debris",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mock": True,
            "detections": mock.get("debris_detections", []),
        }
    from models.debris.inference import run
    try:
        return run(payload=req.model_dump())
    except TypeError:
        return run(req.model_dump())


@app.get("/api/forecast/algal")
def forecast_algal(days: int = 5):
    """Algal bloom forecast for the monitored zone."""
    if USE_MOCK:
        data = _load_mock("algal.json")
        data["requested_days"] = days
        return data
    from models.algal.inference import run
    try:
        return run(payload={"days": days})
    except TypeError:
        return run({"days": days})


@app.post("/api/predict/drift")
def predict_drift(req: DriftRequest):
    """Simple drift trajectory for a spill/debris source point (no heavy model)."""
    if USE_MOCK:
        lon0, lat0 = req.source
        traj = [[lon0, lat0]]
        # crude mock drift: ~0.05 deg/hr east-northeast
        for h in range(1, req.hours + 1, max(1, req.hours // 12)):
            traj.append([round(lon0 + 0.05 * h, 4), round(lat0 + 0.02 * h, 4)])
        return {
            "source": req.source,
            "hours": req.hours,
            "trajectory": traj,
            "mock": True,
        }
    # Real path can use numpy for particle advection; keep light for s390x.
    import numpy as np
    lon0, lat0 = req.source
    steps = max(1, req.hours)
    traj = np.column_stack([
        lon0 + 0.05 * np.arange(steps + 1),
        lat0 + 0.02 * np.arange(steps + 1),
    ]).round(4).tolist()
    return {"source": req.source, "hours": req.hours, "trajectory": traj, "mock": False}


@app.get("/api/priorities")
def priorities():
    """Response priorities ranked by fusion of detection/forecast signals."""
    if USE_MOCK:
        return _load_mock("priorities.json")
    from services import fusion
    return fusion.run_fusion()


@app.post("/api/report")
def submit_report(req: ReportRequest):
    """Accept a citizen/operator pollution report."""
    report_id = str(uuid.uuid4())
    record = {
        "report_id": report_id,
        **req.model_dump(),
        "received_at": datetime.now(timezone.utc).isoformat(),
        "status": "queued",
        "mock": USE_MOCK,
    }
    if not USE_MOCK:
        # Real path: persist to DB / forward to queue. Placeholder for now.
        pass
    return record


@app.get("/api/alerts")
def alerts():
    """Active alerts from the fusion service."""
    from services import fusion
    if USE_MOCK:
        # Mock file is authoritative for demo data; fusion stub is bypassed.
        return _load_mock("alerts.json")
    return fusion.run_fusion()


@app.get("/api/response-impact")
def response_impact():
    """Estimated impact of candidate response actions (skimming, booming, etc.)."""
    if USE_MOCK:
        return _load_mock("response_impact.json")
    from services import fusion
    return fusion.run_fusion()


# ------------------------- frontend serving -------------------------

if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {"message": "Marine Pollution AI API. Frontend/dist not found.", "docs": "/docs"}
