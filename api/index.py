from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import statistics
import os

app = FastAPI()

# Enable CORS for POST requests from any origin
# Vercel sometimes needs explicit handling or starlette middleware behavior
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load data on startup
DATA = []
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "q-vercel-latency.json")
    with open(file_path, "r") as f:
        DATA = json.load(f)
except FileNotFoundError:
    print("Warning: q-vercel-latency.json not found. Make sure to upload it.")

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

@app.get("/api/latency")
def latency_options():
    # Helper for browser testing or OPTIONS requests if needed
    return {"message": "Use POST method"}

@app.post("/api/latency")
async def get_metrics(payload: MetricsRequest):
    results = []
    
    unique_regions = list(set(payload.regions)) 
    
    for region in unique_regions:
        region_data = [d for d in DATA if d.get("region") == region]
        
        if not region_data:
            continue
            
        latencies = [d["latency_ms"] for d in region_data]
        uptimes = [d["uptime_pct"] for d in region_data]
        
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
