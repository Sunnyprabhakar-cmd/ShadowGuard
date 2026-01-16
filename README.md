# 🛡️ Shadow Guard
### ML-Based Network Threat Detection System

> A production-grade, microservices-based network threat detection and automated response platform — built for real-time cybersecurity operations.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)](https://docs.docker.com/compose/)
[![Python](https://img.shields.io/badge/Python-3.11-green?logo=python)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-Express-brightgreen?logo=node.js)](https://nodejs.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3.2-orange?logo=scikit-learn)](https://scikit-learn.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)](https://postgresql.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-teal?logo=fastapi)](https://fastapi.tiangolo.com)

---

## 📌 Overview

Shadow Guard is a fully containerised, 11-service microservices platform that ingests raw network traffic, extracts 69-dimensional feature vectors, applies dual machine learning models for threat detection, and triggers automated incident responses — all within a **sub-100 ms end-to-end latency budget**.

The system covers the complete threat detection lifecycle:

```
Raw Traffic → Feature Extraction → Anomaly Detection → Threat Classification
           → Playbook Decision → Alerting + IP Blocking → PostgreSQL Logging
                                                        → Real-Time Dashboard
```

Built as a B.Tech. final-year project (CS 300) at the **Indian Institute of Information Technology Guwahati**, April 2026.

---

## ✨ Key Features

| Feature | Detail |
|---|---|
| 🔍 **Dual ML Pipeline** | Isolation Forest (unsupervised anomaly detection) + Random Forest (supervised threat classification) |
| ⚡ **Sub-100ms Latency** | Full 11-service pipeline processes each event end-to-end in under 100ms |
| 🐳 **Fully Containerised** | 11 independently deployable Docker services orchestrated with Docker Compose |
| 📊 **Real-Time Dashboard** | React 18 SPA with WebSocket-driven live threat monitoring |
| 🤖 **Automated Response** | IP blocking via iptables, email/Slack alerting, forensic logging |
| 🔁 **Hot-Reload Playbooks** | Update response rules at runtime without restarting services |
| 🧪 **Demo Suite** | 8 realistic attack scenario generators for stakeholder presentations |
| 🗄️ **Persistent Logging** | All threat events stored in PostgreSQL with full audit trail |

---

## 🏗️ Architecture

Shadow Guard follows a **microservices architecture** where each concern is isolated into its own container, communicating exclusively via RESTful HTTP APIs over a private Docker bridge network.

### System Context

```
Demo Traffic Generator
        │
        ▼ POST /capture
┌─────────────────────────────────┐
│  Traffic Capture Service (3001) │
└────────────────┬────────────────┘
                 │ POST /extract
                 ▼
┌─────────────────────────────────┐
│  Feature Extraction Svc  (3002) │  ← 69-dimensional feature vector
└────────────────┬────────────────┘
                 │ POST /detect
                 ▼
┌─────────────────────────────────┐
│  ML Detection Service    (8001) │  ← Isolation Forest
└────────────────┬────────────────┘
          (if anomaly)
                 │ POST /classify
                 ▼
┌─────────────────────────────────┐
│  Threat Classification   (8002) │  ← Random Forest
└────────────────┬────────────────┘
                 │ POST /decide
                 ▼
┌─────────────────────────────────┐
│  Playbook Decision Engine (3003)│
└───────────┬────────────┬────────┘
            │            │
     POST /alert   POST /respond
            ▼            ▼
    ┌────────────┐ ┌──────────────┐
    │   Alert    │ │  Automated   │
    │   Svc      │ │  Response    │
    │  (3004)    │ │  Svc (3005)  │
    └────────────┘ └──────┬───────┘
                          │ POST /log
                          ▼
               ┌─────────────────────┐
               │  Threat Log DB Svc  │ ← PostgreSQL
               │       (3006)        │
               └─────────────────────┘
                          ▲
                          │ WebSocket + HTTP
               ┌─────────────────────┐
               │  React Dashboard    │
               │       (7000)        │
               └─────────────────────┘
```

### Service Topology

| Service | Language | Port | Responsibility |
|---|---|---|---|
| Traffic Capture Service | Node.js / Express | 3001 | Entry point; validates and forwards raw traffic events |
| Flow Feature Extraction | Node.js / Express | 3002 | Computes 69-dimensional ML feature vectors |
| ML Detection Service | Python / FastAPI | 8001 | Isolation Forest anomaly detection |
| Threat Classification Service | Python / FastAPI | 8002 | Random Forest multi-class threat classification |
| Playbook Decision Engine | Node.js / Express | 3003 | JSON rule engine: monitor / alert / block |
| Alert Notification Service | Node.js / Express | 3004 | SMTP email alerting |
| Automated Response Service | Node.js / Express | 3005 | IP blocking (iptables or in-memory) |
| Threat Log DB Service | Node.js / Express | 3006 | REST wrapper over PostgreSQL |
| Model Training Service | Python / FastAPI | 8003 | Trains Isolation Forest + Random Forest |
| Threat Dashboard Service | Node.js / Express | 7000 | React + WebSocket real-time monitoring UI |
| Demo Traffic Generator | Python (internal) | — | Cycles through 8 attack scenarios |

---

## 🤖 Machine Learning Pipeline

Shadow Guard implements a **two-stage hybrid ML pipeline**:

### Stage 1 — Isolation Forest (Unsupervised)
- Detects statistical anomalies in network flows without requiring labelled data
- `contamination = 0.05` (calibrated to 5% anomaly rate)
- `n_estimators = 100`
- Threshold tuned via F1 maximisation on a validation set

### Stage 2 — Random Forest (Supervised)
- Activated only when Stage 1 flags an anomaly
- Classifies confirmed anomalies into specific threat types
- Outputs a `confidence` score (0.0–1.0) and recommended action

### Threat Types Detected
- `ddos` — Distributed Denial of Service
- `port_scan` — Port Reconnaissance
- `data_exfiltration` — Outbound Data Theft
- `brute_force` — Login Brute Force
- `malware_command_control` — C&C Beaconing
- `normal_traffic` — Benign

### Feature Engineering (69-Dimensional Vector)
The Feature Extraction Service constructs a rich non-linear feature space from 3 primary measurements (`packets`, `bytes`, `duration`):

| Category | Count | Description |
|---|---|---|
| Basic stats | 4 | packets, bytes, duration, bytes/sec |
| Packet-based | 10 | packets/sec, avg bytes/pkt, log transforms, interaction terms |
| Statistical | 15 | Sine-based transformations |
| Polynomial | 15 | Power-law combinations |
| Trigonometric/Exponential | 15 | cos() × exp(-duration) terms |
| Padding | 10 | Ensures exactly 69 features |

### Model Performance (Synthetic Dataset)
| Model | Metric | Value |
|---|---|---|
| Random Forest | Accuracy (train/test split) | 85–95% |
| Isolation Forest | Anomaly Detection Rate | Calibrated to 5% contamination |
| Normal Traffic (Scenario 4) | False Positives | 0 |

---

## 📁 Repository Structure

```
shadow_guard/
├── docker-compose.yml              # 11-service stack definition
├── generate_data.py                # Synthetic training data generator
├── generate_traffic.py             # Manual traffic sender
├── auto_demo.py                    # Continuous demo traffic generator
├── demo_log_generator.py           # Interactive attack simulator
├── demo_checklist.py               # Pre-demo validation (18 checks)
├── start_demo.sh                   # One-command bootstrap (Linux/macOS)
├── start_demo.ps1                  # PowerShell bootstrap (Windows)
├── .env.example                    # Environment variable template
├── data/
│   └── sample_traffic.parquet      # Synthetic training data
├── models/
│   ├── isolation_forest_model.pkl
│   └── random_forest_model.pkl
├── database/
│   └── init.sql                    # PostgreSQL schema
├── traffic-capture-service/
├── flow-feature-extraction-service/
├── ml-detection-service/
├── threat-classification-service/
├── playbook-decision-engine/
│   └── rules/
│       └── playbook-rules.json
├── alert-notification-service/
├── automated-response-service/
├── threat-log-database-service/
├── model-training-service/
└── threat-dashboard-service/
    └── public/
        ├── index.html
        ├── app.js
        └── styles.css
```

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Version |
|---|---|
| Docker Engine | ≥ 24.0 |
| Docker Compose | v2 |
| Python | 3.9+ |
| Git | Any |

### Linux / macOS

```bash
# 1. Clone the repository
git clone <repo-url> && cd shadow_guard

# 2. Generate synthetic training data
python3 generate_data.py
# Creates ./data/sample_traffic.parquet (1000 samples, 5% anomaly rate)

# 3. (Optional) Configure email alerts
cp .env.example .env
# Edit EMAIL_USER, EMAIL_PASS, ALERT_RECIPIENTS

# 4. Train the ML models
docker-compose up model-training-service
# Wait for: "Training complete. Models saved to /app/models"
# Then Ctrl+C

# 5. Start all services
docker-compose up -d

# 6. Verify all services are healthy
docker-compose ps
curl http://localhost:7000/health

# 7. Open the dashboard
open http://localhost:7000          # macOS
xdg-open http://localhost:7000      # Linux
```

### Windows (PowerShell)

```powershell
# 1. Prerequisites: Docker Desktop, Python 3.x, Git

# 2. Clone
git clone <repo-url>; cd shadow_guard

# 3. Generate training data
python generate_data.py

# 4. Train models
docker compose up model-training-service
# Wait for completion, then Ctrl+C

# 5. Start full stack
docker compose up -d

# 6. Open dashboard
Start-Process 'http://localhost:7000'
```

### One-Command Bootstrap

```bash
./start_demo.sh    # Linux/macOS
.\start_demo.ps1   # Windows PowerShell
```

This script automatically handles: dependency checking → stack startup → model training → health verification → smoke test → demo log reset → dashboard launch.

---

## 🎭 Demo Attack Scenarios

The demo suite ships with 8 realistic attack scenario generators:

| # | Scenario | Description | Expected Confidence | Action |
|---|---|---|---|---|
| 1 | Port Scan | 6 sequential TCP probes to different ports | ~0.75 | Alert |
| 2 | DDoS Attack | 5 botnet IPs, 5000+ UDP packets each | >0.90 | Block |
| 3 | Data Exfiltration | 3 large TCP bursts, 50 MB+ per burst | ~0.88 | Block |
| 4 | Normal Traffic | Web browsing, DNS, cloud sync, streaming | <0.30 | Monitor |
| 5 | Brute Force | 8 rapid sequential TCP connections, tiny payloads | ~0.72 | Alert |
| 6 | Malware C&C | 4 irregular beaconing events to external IP | ~0.80 | Block |
| 7 | Multi-Vector | Simultaneous port scan + DDoS + exfiltration | >0.90 | Block all |
| 8 | Zero-Day Exploit | 4-phase chain: probe → payload → escalation → beacon | >0.90 | Block |

### Running the Demo

```bash
# Pre-demo validation (run 30 minutes before presenting)
python3 demo_checklist.py
# Runs 18 automated checks: Docker, all service health endpoints, DB, models, APIs

# Interactive attack simulator
python3 demo_log_generator.py
# Select scenarios 1–9 from interactive menu

# Continuous background demo (runs automatically in Docker)
docker-compose up -d demo-traffic-generator
docker-compose logs -f demo-traffic-generator

# Simple traffic sender
python3 generate_traffic.py
# Sends 5 predefined patterns: benign / suspicious / high-risk
```

---

## 🗄️ Database Schema

Shadow Guard uses **PostgreSQL 15** with a single append-optimised event log table:

```sql
CREATE TABLE threat_logs (
    id           SERIAL PRIMARY KEY,
    timestamp    TIMESTAMP DEFAULT NOW(),
    src_ip       VARCHAR(45),
    dst_ip       VARCHAR(45),
    protocol     VARCHAR(10),      -- TCP, UDP, ICMP
    packets      INTEGER,
    bytes        BIGINT,
    duration     FLOAT,
    threat_type  VARCHAR(100),     -- ddos, port_scan, brute_force, etc.
    confidence   FLOAT,            -- 0.0 to 1.0
    action       VARCHAR(50),      -- block, alert, monitor
    anomaly_score FLOAT,
    is_anomaly   BOOLEAN,
    attack_type  VARCHAR(100),
    flow_type    VARCHAR(50),
    status       VARCHAR(50)
);
```

#### Useful Queries

```sql
-- Last 100 threats
SELECT * FROM threat_logs ORDER BY timestamp DESC LIMIT 100;

-- Count by threat type
SELECT threat_type, COUNT(*) FROM threat_logs GROUP BY threat_type;

-- High-confidence threats (block-worthy)
SELECT * FROM threat_logs WHERE confidence > 0.8;

-- Blocked IPs
SELECT DISTINCT src_ip FROM threat_logs WHERE action = 'block';

-- Alerts in last 24 hours
SELECT COUNT(*) FROM threat_logs
WHERE action = 'alert' AND timestamp > NOW() - INTERVAL '1 day';
```

---

## 🔧 Playbook Decision Engine

Response actions are determined by confidence score thresholds, defined in `playbook-rules.json`:

| Confidence Range | Action | Effect |
|---|---|---|
| < 0.30 | `monitor` | Log only, no alert |
| 0.30 – 0.80 | `alert` | Send email/Slack notification to SOC |
| > 0.80 | `block` | Automated IP blocking + alert + log |

Rules can be hot-reloaded without restarting:

```bash
# Edit playbook-decision-engine/rules/playbook-rules.json
curl -X POST http://localhost:3003/reload-rules
```

---

## 🔐 Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Key variables:

| Variable | Service | Required | Notes |
|---|---|---|---|
| `EMAIL_USER` | Alert | Optional | SMTP username |
| `EMAIL_PASS` | Alert | Optional | SMTP password — treat as secret |
| `SMTP_HOST` | Alert | Optional | SMTP server hostname |
| `SMTP_PORT` | Alert | Optional | e.g., 587 |
| `ALERT_RECIPIENTS` | Alert | Optional | Comma-separated email list |
| `ALERT_CRITICAL_ONLY` | Alert | Optional | `true` = block-level alerts only |
| `DB_HOST` | DB Svc | Required | PostgreSQL hostname |
| `DB_USER` | DB Svc | Required | PostgreSQL username |
| `DB_PASS` | DB Svc | Required | **Change in production** |
| `DB_NAME` | DB Svc | Required | Database name |
| `ENABLE_LOCAL_IPTABLES` | Response | Optional | `true` for real firewall blocking (needs root) |
| `MODEL_PATH` | ML services | Required | Path to `/app/models` |
| `PLAYBOOK_RULES_PATH` | Playbook | Required | Path to rules JSON |

> ⚠️ **Never commit `.env` to version control.** The default `POSTGRES_PASSWORD=password` must be changed before any non-local deployment.

---

## 📊 Performance Characteristics

| Metric | Value |
|---|---|
| End-to-end pipeline latency | < 100 ms per event |
| ML inference latency (both models) | < 50 ms per event |
| Dashboard WebSocket latency | < 1 second |
| Node.js service memory | ~50 MB at rest |
| Python ML service memory | ~150–300 MB |
| Node.js service throughput | 100–1,000 events/sec per instance |
| Dashboard concurrent users | 50+ with single instance |

---

## 🔑 Operational Commands

```bash
# View real-time logs for a service
docker-compose logs -f threat-dashboard-service

# Restart a failed service
docker-compose restart ml-detection-service

# Rebuild a single service after code changes
docker-compose up -d --build ml-detection-service

# Scale feature extraction to 3 instances
docker-compose up -d --scale flow-feature-extraction-service=3

# Re-train models (add new Parquet files to ./data/ first)
docker-compose up model-training-service
docker-compose restart ml-detection-service threat-classification-service

# Reset demo threat logs
curl -X POST http://localhost:3006/logs/reset -H 'Content-Type: application/json' -d '{}'

# Export threat logs
curl http://localhost:7000/api/export/logs > threats-$(date +%Y%m%d).json

# Direct database access
docker-compose exec postgres psql -U user threat_logs

# Database backup
docker exec shadow_guard-postgres-1 pg_dump -U user threat_logs > backup.sql

# Tear down (preserves DB volume)
docker-compose down

# Full teardown including volumes (deletes all data)
docker-compose down -v
```

---

## 🐛 Troubleshooting

| Error | Resolution |
|---|---|
| Port already in use (3001, 7000) | `lsof -i :3001` then `kill -9 <PID>` |
| Model not found (HTTP 500 on `/detect`) | Run `docker-compose up model-training-service` first |
| `postgres` not healthy | Wait 30s for DB init, or `docker-compose restart postgres` |
| Dashboard shows no threats | Check: `curl http://localhost:3001/health` |
| Connection refused from generator | Check: `docker-compose logs traffic-capture-service` |
| Permission denied (iptables) | Set `ENABLE_LOCAL_IPTABLES=false` or run container with `--privileged` |

---

## 🔒 Security Notes

> ⚠️ This project is designed for **development and demonstration** purposes. Before any production deployment:

**Critical (P0)**
- Change all default database credentials (`user` / `password`)
- Add JWT or API key authentication to the dashboard and capture service endpoints

**High (P1)**
- Enable HTTPS via a reverse proxy (Nginx / Traefik)
- Move `EMAIL_PASS` and `SMTP_PASS` to Docker Secrets or a secrets manager

**Medium (P2)**
- Add rate limiting to `POST /capture` (e.g., `express-rate-limit`)
- Configure CORS to allow only trusted origins on the dashboard
- Add `Helmet.js` security headers to all Node.js services

**Low (P3)**
- Implement model file integrity verification (hash check on load)
- Replace `console.log()` with structured JSON logging for SIEM integration

---

## 🔭 Recommended Production Monitoring Stack

- **Prometheus** — expose `/metrics` on each service
- **Grafana** — panels for events/sec, pipeline latency P50/P95/P99, threat type breakdown
- **Loki + Promtail** — centralised log aggregation from Docker stdout
- **Alertmanager** — alert on non-200 health checks, latency > 500ms, DB connection failures

---

## 🔬 Training with Real Data

For production deployments, the following benchmark datasets are recommended:

| Dataset | Source |
|---|---|
| CIC-IDS2017 | [Canadian Institute for Cybersecurity](https://www.unb.ca/cic/datasets/) |
| UNSW-NB15 | [UNSW Research](https://research.unsw.edu.au/projects/unsw-nb15-dataset) |
| KDD CUP 99 | [UCI Repository](http://kdd.ics.uci.edu/databases/kddcup99/) |

Place `.parquet` files in `./data/` and retrain:

```bash
docker-compose up model-training-service
```

---

## 📚 References

1. Chen et al. (2021). ADASYN-Random Forest Based Intrusion Detection Model. *arXiv*.
2. Zhang et al. (2008). Random-Forests-Based Network Intrusion Detection Systems. *IEEE*.
3. Liu, Ting & Zhou (2008). Isolation Forest. *IEEE ICDM*. https://doi.org/10.1109/ICDM.2008.17
4. Chandola, Banerjee & Kumar (2009). Anomaly Detection: A Survey. *ACM*.
5. Sharafaldin et al. (2018). CICIDS2017 Dataset. *SCITEPRESS*.
6. Breiman (2001). Random Forests. *Machine Learning Journal*.
7. Patcha & Park (2007). An overview of anomaly detection techniques. *Computer Networks*.
8. Sommer & Paxson (2010). Machine learning for intrusion detection. *IEEE S&P*.

---

## 👩‍💻 Author

**Sunny Prabhakar** 
