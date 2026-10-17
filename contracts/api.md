# API contract (tell the whole team before changing anything)

Base URL: set in VITE_API_URL (frontend) 

| Endpoint | Method | Gives back |
|---|---|---|
| /api/health | GET | {"status":"ok"} |
| /api/scenario | GET | Everything for the demo in one go (safety net) |
| /api/detect/oil | POST | GeoJSON oil outlines with area_km2, confidence |
| /api/detect/debris | POST | List of {lat, lon, class, confidence, bbox} |
| /api/forecast/algal | GET ?station_id=S1 | history, forecast, risk |
| /api/predict/drift | POST | Dots at 24, 48, 72 h + fraction reaching each zone |
| /api/priorities | GET | Ranked list: rank, type, score, reason, eta_landfall_h, confidence, sources |
| /api/alerts | GET | List of alerts (shape below) |
| /api/response-impact | GET ?delay_hours=12 | fraction_already_ashore, fraction_still_at_sea, zones_hit_before_response, zones_still_protectable |
| /api/report | POST {event_id} | {"text": "..."} |

## Alert shape

{
  "id": "A1",
  "event_id": "E1",
  "severity": "info | warning | critical",
  "rule": "R1",
  "sources": ["satellite", "drone"],
  "message": "Oil patch detected with 72% confidence. Needs verification.",
  "action": "Send drone to survey the suggested area.",
  "location": { "lat": 13.20, "lon": 80.35 },
  "suggested_area": [80.33, 13.18, 80.37, 13.22]
}

## Response-impact shape

{
  "delay_hours": 12,
  "fraction_already_ashore": 0.18,
  "fraction_still_at_sea": 0.82,
  "zones_hit_before_response": [{"zone": "Reef A", "hour": 9}],
  "zones_still_protectable": ["Port B", "Mangrove C"]
}
