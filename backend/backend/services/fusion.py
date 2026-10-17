"""Sensor/model fusion service (STUB).

Teammate will implement run_fusion() to combine oil detection, debris
detection and algal forecasts into alerts / priorities / response-impact.
The backend imports this module lazily so mock mode never touches it.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

MOCK_DIR = Path(__file__).resolve().parent.parent / "mock_data"


def run_fusion(payload: dict | None = None) -> dict:
    """Stub: returns alerts.json, or a minimal placeholder if missing."""
    alerts_path = MOCK_DIR / "alerts.json"
    if alerts_path.exists():
        with open(alerts_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stub": True,
        "alerts": [],
        "note": "fusion.run_fusion is a stub awaiting teammate implementation",
    }
