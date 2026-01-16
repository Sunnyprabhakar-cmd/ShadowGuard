#!/usr/bin/env bash
# Shadow Guard - One-command demo bootstrap
# Builds the stack, verifies health, trains compatible models, opens the dashboard,
# and launches the auto traffic generator.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log() {
    printf "[start_demo] %s\n" "$1"
}

fail() {
    printf "[start_demo][error] %s\n" "$1" >&2
    exit 1
}

require_cmd() {
    local cmd="$1"
    local help_text="$2"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        fail "$help_text"
    fi
}

pick_python() {
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
    else
        fail "Python is required to run the demo scripts."
    fi
}

pick_docker_compose() {
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE=("docker" "compose")
    elif command -v docker-compose >/dev/null 2>&1; then
        DOCKER_COMPOSE=("docker-compose")
    else
        fail "Docker Compose was not found. Install Docker Desktop or docker-compose."
    fi
}

ensure_data_exists() {
    if ! find "$SCRIPT_DIR/data" -maxdepth 1 -type f -name "*.parquet" | grep -q .; then
        fail "No parquet files found in data/. Add training data before running the demo."
    fi
}

stop_existing_local_demo() {
    local pid_file="$SCRIPT_DIR/auto_demo.pid"
    local log_file="$SCRIPT_DIR/auto_demo.log"

    if [[ -f "$pid_file" ]]; then
        local existing_pid
        existing_pid="$(cat "$pid_file" 2>/dev/null || true)"
        if [[ -n "$existing_pid" ]] && kill -0 "$existing_pid" >/dev/null 2>&1; then
            log "Stopping previous local auto demo process $existing_pid"
            kill "$existing_pid" >/dev/null 2>&1 || true
        fi
        rm -f "$pid_file"
    fi

    : > "$log_file"
}

start_stack() {
    log "Starting services with local images first"
    if "${DOCKER_COMPOSE[@]}" up -d; then
        return 0
    fi

    log "Local startup failed, retrying with a rebuild"
    "${DOCKER_COMPOSE[@]}" up -d --build
}

wait_for_health() {
    "$PYTHON_CMD" - <<'PY'
import time
from urllib.request import urlopen

urls = [
    "http://localhost:3001/health",
    "http://localhost:3002/health",
    "http://localhost:3003/health",
    "http://localhost:3004/health",
    "http://localhost:3005/health",
    "http://localhost:3006/health",
    "http://localhost:7000",
    "http://localhost:8001/health",
    "http://localhost:8002/health",
    "http://localhost:8003/health",
]

deadline = time.time() + 180
pending = set(urls)

while time.time() < deadline and pending:
    for url in list(pending):
        try:
            with urlopen(url, timeout=4) as response:
                if response.status == 200:
                    pending.remove(url)
        except Exception:
            pass
    if pending:
        time.sleep(2)

if pending:
    raise SystemExit("Services not healthy in time: " + ", ".join(sorted(pending)))
PY
}

verify_models_loaded() {
    "$PYTHON_CMD" - <<'PY'
import json
import time
from urllib.request import urlopen

endpoints = ("http://localhost:8001/health", "http://localhost:8002/health")
deadline = time.time() + 90
last_error = None

while time.time() < deadline:
    all_loaded = True
    for endpoint in endpoints:
        try:
            with urlopen(endpoint, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
                print(endpoint, payload)
                if payload.get("model_loaded") is not True:
                    all_loaded = False
                    last_error = f"Model not loaded on {endpoint}"
        except Exception as exc:
            all_loaded = False
            last_error = str(exc)
    if all_loaded:
        raise SystemExit(0)
    time.sleep(2)

raise SystemExit(last_error or "Models failed to load in time")
PY
}

smoke_test_pipeline() {
    "$PYTHON_CMD" - <<'PY'
import json
from urllib.request import Request, urlopen

payload = {
    "packets": 120,
    "bytes": 8192,
    "duration": 3.4,
    "ip": "198.51.100.25",
}

request = Request(
    "http://localhost:3001/capture",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urlopen(request, timeout=20) as response:
    print("Pipeline status:", response.status)
    print("Pipeline body:", response.read().decode("utf-8"))
PY
}

reset_threat_logs() {
    "$PYTHON_CMD" - <<'PY'
import json
from urllib.request import Request, urlopen

request = Request(
    "http://localhost:3006/logs/reset",
    data=b"{}",
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urlopen(request, timeout=20) as response:
    print("Threat log reset:", response.read().decode("utf-8"))
PY
}

open_dashboard() {
    local url="http://localhost:7000"

    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$url" >/dev/null 2>&1 &
        log "Opened dashboard in your browser: $url"
    elif command -v open >/dev/null 2>&1; then
        open "$url" >/dev/null 2>&1 &
        log "Opened dashboard in your browser: $url"
    elif command -v cmd.exe >/dev/null 2>&1; then
        cmd.exe /c start "$url" >/dev/null 2>&1 &
        log "Opened dashboard in your browser: $url"
    elif command -v powershell.exe >/dev/null 2>&1; then
        powershell.exe -NoProfile -Command "Start-Process '$url'" >/dev/null 2>&1 &
        log "Opened dashboard in your browser: $url"
    else
        log "Open the dashboard manually in your browser: $url"
    fi
}

launch_demo() {
    if "${DOCKER_COMPOSE[@]}" ps demo-traffic-generator 2>/dev/null | grep -q "Up"; then
        log "Docker demo traffic generator is running"
        log "Traffic generator logs: ${DOCKER_COMPOSE[*]} logs -f demo-traffic-generator"
        return 0
    fi

    local log_file="$SCRIPT_DIR/auto_demo.log"
    local pid_file="$SCRIPT_DIR/auto_demo.pid"
    local demo_cmd="cd '$SCRIPT_DIR' && exec '$PYTHON_CMD' auto_demo.py"

    if [[ -f "$pid_file" ]]; then
        local existing_pid
        existing_pid="$(cat "$pid_file" 2>/dev/null || true)"
        if [[ -n "$existing_pid" ]] && kill -0 "$existing_pid" >/dev/null 2>&1; then
            log "Auto demo is already running with PID $existing_pid"
            log "Traffic generator log: $log_file"
            return 0
        fi
    fi

    if command -v setsid >/dev/null 2>&1; then
        setsid bash -lc "$demo_cmd" >"$log_file" 2>&1 < /dev/null &
    else
        nohup bash -lc "$demo_cmd" >"$log_file" 2>&1 < /dev/null &
    fi

    local demo_pid=$!
    sleep 2
    if ! kill -0 "$demo_pid" >/dev/null 2>&1; then
        rm -f "$pid_file"
        fail "Auto demo failed to stay running. Check $log_file for details."
    fi

    printf "%s\n" "$demo_pid" > "$pid_file"
    log "Auto demo started in the background with PID $demo_pid"
    log "Traffic generator log: $log_file"
}

main() {
    echo "=================================="
    echo " Shadow Guard - Demo Quick Start"
    echo "=================================="
    echo

    require_cmd docker "Docker is required to run the demo."
    pick_docker_compose
    pick_python
    ensure_data_exists
    stop_existing_local_demo

    start_stack

    log "Waiting for services to become healthy"
    wait_for_health

    log "Training models inside the container"
    "${DOCKER_COMPOSE[@]}" exec -T model-training-service python train_model.py

    log "Reloading inference services with the freshly trained models"
    "${DOCKER_COMPOSE[@]}" restart ml-detection-service threat-classification-service

    log "Verifying model load"
    verify_models_loaded

    log "Running end-to-end smoke test"
    smoke_test_pipeline

    log "Resetting old threat logs for a clean live demo"
    reset_threat_logs

    log "Ensuring demo traffic generator is running"
    "${DOCKER_COMPOSE[@]}" up -d demo-traffic-generator

    open_dashboard
    launch_demo

    echo
    echo "=========================================="
    echo " Shadow Guard demo is ready"
    echo "=========================================="
    echo
    echo "Dashboard: http://localhost:7000"
    echo "Auto traffic generator: running"
    echo "Traffic generator logs: ${DOCKER_COMPOSE[*]} logs -f demo-traffic-generator"
    echo
    echo "Useful commands:"
    echo "  ${DOCKER_COMPOSE[*]} logs -f <service>"
    echo "  ${DOCKER_COMPOSE[*]} down"
    echo "  $PYTHON_CMD demo_log_generator.py"
}

main "$@"
