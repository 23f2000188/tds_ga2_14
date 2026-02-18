from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Embedded telemetry data
DATA = [
  {"region":"apac","service":"payments","latency_ms":166.7,"uptime_pct":98.528,"timestamp":20250301},
  {"region":"apac","service":"recommendations","latency_ms":164.81,"uptime_pct":97.866,"timestamp":20250302},
  {"region":"apac","service":"analytics","latency_ms":154.76,"uptime_pct":98.072,"timestamp":20250303},
  {"region":"apac","service":"checkout","latency_ms":156.15,"uptime_pct":97.362,"timestamp":20250304},
  {"region":"apac","service":"analytics","latency_ms":131.08,"uptime_pct":99.243,"timestamp":20250305},
  {"region":"apac","service":"catalog","latency_ms":224.93,"uptime_pct":97.186,"timestamp":20250306},
  {"region":"apac","service":"catalog","latency_ms":142.86,"uptime_pct":97.721,"timestamp":20250307},
  {"region":"apac","service":"recommendations","latency_ms":185.92,"uptime_pct":98.18,"timestamp":20250308},
  {"region":"apac","service":"recommendations","latency_ms":206.88,"uptime_pct":98.213,"timestamp":20250309},
  {"region":"apac","service":"payments","latency_ms":160.23,"uptime_pct":99.003,"timestamp":20250310},
  {"region":"apac","service":"analytics","latency_ms":211.17,"uptime_pct":98.973,"timestamp":20250311},
  {"region":"apac","service":"payments","latency_ms":183.81,"uptime_pct":98.791,"timestamp":20250312},
  {"region":"emea","service":"support","latency_ms":159.89,"uptime_pct":98.656,"timestamp":20250301},
  {"region":"emea","service":"support","latency_ms":121.51,"uptime_pct":99.426,"timestamp":20250302},
  {"region":"emea","service":"support","latency_ms":210.08,"uptime_pct":98.879,"timestamp":20250303},
  {"region":"emea","service":"catalog","latency_ms":227.34,"uptime_pct":98.998,"timestamp":20250304},
  {"region":"emea","service":"payments","latency_ms":233.37,"uptime_pct":97.975,"timestamp":20250305},
  {"region":"emea","service":"payments","latency_ms":119.26,"uptime_pct":99.45,"timestamp":20250306},
  {"region":"emea","service":"analytics","latency_ms":202.75,"uptime_pct":98.498,"timestamp":20250307},
  {"region":"emea","service":"catalog","latency_ms":208.56,"uptime_pct":98.176,"timestamp":20250308},
  {"region":"emea","service":"payments","latency_ms":134.1,"uptime_pct":99.196,"timestamp":20250309},
  {"region":"emea","service":"catalog","latency_ms":182.67,"uptime_pct":97.707,"timestamp":20250310},
  {"region":"emea","service":"recommendations","latency_ms":127.35,"uptime_pct":98.233,"timestamp":20250311},
  {"region":"emea","service":"checkout","latency_ms":133.3,"uptime_pct":97.343,"timestamp":20250312},
  {"region":"amer","service":"support","latency_ms":215.34,"uptime_pct":98.825,"timestamp":20250301},
  {"region":"amer","service":"support","latency_ms":153.54,"uptime_pct":98.331,"timestamp":20250302},
  {"region":"amer","service":"catalog","latency_ms":144.12,"uptime_pct":98.404,"timestamp":20250303},
  {"region":"amer","service":"payments","latency_ms":124.43,"uptime_pct":97.181,"timestamp":20250304},
  {"region":"amer","service":"support","latency_ms":157.74,"uptime_pct":98.437,"timestamp":20250305},
  {"region":"amer","service":"analytics","latency_ms":136.94,"uptime_pct":98.59,"timestamp":20250306},
  {"region":"amer","service":"recommendations","latency_ms":209.87,"uptime_pct":98.129,"timestamp":20250307},
  {"region":"amer","service":"catalog","latency_ms":211.02,"uptime_pct":97.99,"timestamp":20250308},
  {"region":"amer","service":"payments","latency_ms":101.78,"uptime_pct":99.399,"timestamp":20250309},
  {"region":"amer","service":"payments","latency_ms":157.35,"uptime_pct":97.822,"timestamp":20250310},
  {"region":"amer","service":"analytics","latency_ms":119.75,"uptime_pct":98.792,"timestamp":20250311},
  {"region":"amer","service":"support","latency_ms":167.74,"uptime_pct":98.097,"timestamp":20250312},
]

@app.options("/api/metrics")
async def options_metrics():
    return JSONResponse(content={}, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    })

@app.post("/api/metrics")
async def get_metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    result = {}
    for region in regions:
        records = [d for d in DATA if d["region"] == region]
        if not records:
            result[region] = {"error": "No data found"}
            continue
        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]
        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 4),
            "p95_latency": round(float(np.percentile(latencies, 95)), 4),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": int(sum(1 for l in latencies if l > threshold_ms)),
        }

    response = JSONResponse(content=result)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
