import json
import os
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# load telemetry from file (recommended)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # project root
DATA_PATH = os.path.join(BASE_DIR, "q-vercel-latency.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    DATA = json.load(f)

@app.post("/")
def latency(payload: dict):
    regions = payload.get("regions", [])
    threshold_ms = payload.get("threshold_ms", 180)

    result = {}
    for region in regions:
        records = [r for r in DATA if r.get("region") == region]
        if not records:
            result[region] = {
                "avg_latency": 0.0,
                "p95_latency": 0.0,
                "avg_uptime": 0.0,
                "breaches": 0,
            }
            continue

        latencies = [float(r["latency_ms"]) for r in records]
        uptimes = [float(r["uptime_pct"]) for r in records]

        result[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": int(sum(1 for x in latencies if x > float(threshold_ms))),
        }

    return result
