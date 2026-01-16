#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log() {
  printf "[bootstrap] %s\n" "$1"
}

fail() {
  printf "[bootstrap][error] %s\n" "$1" >&2
  exit 1
}

ensure_data_exists() {
  if ! find "$ROOT_DIR/data" -maxdepth 1 -type f -name "*.parquet" | grep -q .; then
    fail "No parquet files found in data/. Add training files first."
  fi
}

wait_for_health() {
  python - <<'PY'
import json
import time
from urllib.request import urlopen

services = [
    "http://localhost:3001/health",
    "http://localhost:3002/health",
    "http://localhost:3003/health",
    "http://localhost:3004/health",
    "http://localhost:3005/health",
    "http://localhost:3006/health",
    "http://localhost:8001/health",
    "http://localhost:8002/health",
    "http://localhost:8003/health",
]

deadline = time.time() + 120
pending = set(services)

while time.time() < deadline and pending:
    for url in list(pending):
        try:
            with urlopen(url, timeout=3) as r:
                if r.status == 200:
                    pending.remove(url)
        except Exception:
            pass
    if pending:
        time.sleep(2)

if pending:
    raise SystemExit("Services not healthy in time: " + ", ".join(sorted(pending)))

print("All health endpoints are responding")
PY
}

verify_models_loaded() {
  python - <<'PY'
import json
from urllib.request import urlopen

for endpoint in ["http://localhost:8001/health", "http://localhost:8002/health"]:
    with urlopen(endpoint, timeout=5) as r:
        payload = json.loads(r.read().decode("utf-8"))
        loaded = payload.get("model_loaded")
        print(endpoint, payload)
        if loaded is not True:
            raise SystemExit(f"Model not loaded on {endpoint}")
PY
}

smoke_test_pipeline() {
  python - <<'PY'
import json
from urllib.request import Request, urlopen

payload = {
    "packets": 120,
    "bytes": 8192,
    "duration": 3.4,
    "ip": "198.51.100.25"
}

req = Request(
    "http://localhost:3001/capture",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urlopen(req, timeout=20) as r:
    body = r.read().decode("utf-8")
    print("Pipeline response status:", r.status)
    print("Pipeline response body:", body)
PY
}

log "Starting stack"
docker compose up -d --build

log "Waiting for health endpoints"
wait_for_health

log "Checking dataset presence"
ensure_data_exists

log "Training models"
docker compose exec -T model-training-service python train_model.py

[[ -f "$ROOT_DIR/models/random_forest_model.pkl" ]] || fail "random_forest_model.pkl not found"
[[ -f "$ROOT_DIR/models/isolation_forest_model.pkl" ]] || fail "isolation_forest_model.pkl not found"

log "Restarting inference services to pick up models"
docker compose restart ml-detection-service threat-classification-service

log "Validating models are loaded"
verify_models_loaded

log "Running end-to-end smoke test"
smoke_test_pipeline

log "Bootstrap complete"
