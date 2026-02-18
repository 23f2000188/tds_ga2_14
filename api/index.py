from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import statistics
import os

app = FastAPI()

# We are relying on vercel.json for CORS headers to avoid duplication/conflicts.
# However, for local testing, we add a simple middleware or just leave it.
# To be safe and compliant with the "vercel.json handles it" strategy, 
# we won't add CORSMiddleware here.

# --- DATA LOADING ---
DATA = []
try:
    # Try looking in the same directory as this file (api/q-vercel-latency.json)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "q-vercel-latency.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            DATA = json.load(f)
    else:
        # Fallback to root or other locations
        # For Vercel, it often copies files to the root of the task
        if os.path.exists("q-vercel-latency.json"):
             with open("q-vercel-latency.json", "r") as f:
                DATA = json.load(f)
        elif os.path.exists("api/q-vercel-latency.json"):
             with open("api/q-vercel-latency.json", "r") as f:
                DATA = json.load(f)
except Exception as e:
    print(f"Warning: Could not load data: {e}")

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
    
    # Ensure regions are unique but preserve order if possible or just set
    unique_regions = list(set(payload.regions))
    
    for region in unique_regions:
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

# Explicit options handler just in case vercel passes it through
@app.options("/api/latency")
async def options_handler():
    return {"message": "OK"}
