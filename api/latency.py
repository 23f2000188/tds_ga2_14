import json
import os
from statistics import mean
from typing import List, Dict, Any

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

def _percentile(sorted_vals: List[float], p: float) -> float:
    """
    Linear interpolation percentile (common practical choice).
    p=0.95 => 95th percentile.
    """
    n = len(sorted_vals)
    if n == 0:
        return 0.0
    if n == 1:
        return float(sorted_vals[0])

    # rank in [0, n-1]
    r = (n - 1) * p
    lo = int(r)
    hi = min(lo + 1, n - 1)
    frac = r - lo
    return float(sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac)

def _load_telemetry() -> List[Dict[str, Any]]:
    # File lives at repo root. In Vercel, cwd is project root for the function.
    path = os.path.join(os.getcwd(), "q-vercel-latency.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def handler(request):
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return ("", 204, CORS_HEADERS)

    if request.method != "POST":
        return (json.dumps({"error": "Method not allowed"}), 405, {**CORS_HEADERS, "Content-Type": "application/json"})

    try:
        body = request.get_json()
    except Exception:
        return (json.dumps({"error": "Invalid JSON"}), 400, {**CORS_HEADERS, "Content-Type": "application/json"})

    regions = body.get("regions")
    threshold_ms = body.get("threshold_ms")

    if not isinstance(regions, list) or not all(isinstance(r, str) for r in regions):
        return (json.dumps({"error": "Body must include regions: [..]"}), 400, {**CORS_HEADERS, "Content-Type": "application/json"})

    try:
        threshold_ms = float(threshold_ms)
    except Exception:
        return (json.dumps({"error": "Body must include threshold_ms as a number"}), 400, {**CORS_HEADERS, "Content-Type": "application/json"})

    telemetry = _load_telemetry()

    out: Dict[str, Any] = {}
    for region in regions:
        rows = [r for r in telemetry if r.get("region") == region]
        latencies = [float(r["latency_ms"]) for r in rows if "latency_ms" in r]
        uptimes = [float(r["uptime_pct"]) for r in rows if "uptime_pct" in r]

        lat_sorted = sorted(latencies)
        breaches = sum(1 for v in latencies if v > threshold_ms)

        out[region] = {
            "avg_latency": float(mean(latencies)) if latencies else 0.0,
            "p95_latency": _percentile(lat_sorted, 0.95) if lat_sorted else 0.0,
            "avg_uptime": float(mean(uptimes)) if uptimes else 0.0,
            "breaches": int(breaches),
        }

    return (json.dumps(out), 200, {**CORS_HEADERS, "Content-Type": "application/json"})
