# eShopCo Latency Monitor

FastAPI endpoint deployed on Vercel for monitoring regional service latency.

## POST /api/metrics

**Body:**
```json
{"regions": ["emea", "apac"], "threshold_ms": 169}
```

**Response:**
```json
{
  "emea": {
    "avg_latency": 175.44,
    "p95_latency": 228.07,
    "avg_uptime": 98.59,
    "breaches": 6
  },
  ...
}
```
