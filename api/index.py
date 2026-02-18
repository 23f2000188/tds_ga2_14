from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
import json
import statistics
import os

app = FastAPI()

# --- FORCE CORS HEADERS MANUALLY ---
# This middleware intercepts EVERY request and forces the CORS headers.
# It effectively overrides typical CORS middleware quirks.
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    # 1. Handle Preflight OPTIONS requests immediately
    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

    # 2. Process the actual request
    try:
        response = await call_next(request)
    except Exception as e:
        # If an error occurs, we still want CORS headers on the error response
        print(f"Error: {e}")
        response = Response(content=json.dumps({"detail": str(e)}), status_code=500, media_type="application/json")

    # 3. Add valid CORS headers to the response
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

# --- DATA LOADING ---
DATA = []
try:
    # Use absolute path relative to this file to find the json
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "q-vercel-latency.json")
    with open(file_path, "r") as f:
        DATA = json.load(f)
except Exception as e:
    print(f"Error loading data: {e}")
    # Fallback: try to load from current working directory
    if os.path.exists("q-vercel-latency.json"):
        with open("q-vercel-latency.json", "r") as f:
            DATA = json.load(f)

# --- METRIC LOGIC ---
class MetricsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

def calculate_p95(data):
    if not data:
        return 0.0
    data.sort()
    n = len(data)
    pos = (n - 1) * 0.95
    idx = int(pos)
    rem = pos - idx
    if idx + 1 < n:
        return data[idx] + rem * (data[idx+1] - data[idx])
    else:
        return data[idx]

@app.post("/api/latency")
async def get_metrics(payload: MetricsRequest):
    results = []
    unique_regions = list(set(payload.regions))
    
    for region in unique_regions:
        # Filter data for this region
        region_data = [d for d in DATA if d.get("region") == region]
        
        if not region_data:
            continue
            
        latencies = [d["latency_ms"] for d in region_data]
        uptimes = [d["uptime_pct"] for d in region_data]
        
        if not latencies:
            continue

        avg_latency = statistics.mean(latencies)
        p95_latency = calculate_p95(latencies)
        avg_uptime = statistics.mean(uptimes)
        breaches = len([l for l in latencies if l > payload.threshold_ms])
        
        results.append({
            "region": region,
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 3),
            "breaches": breaches
        })
        
    return {"regions": results}
