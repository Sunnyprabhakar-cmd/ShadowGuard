# Shadow Guard - Live Demo Guide

## Quick Start

### 1. Ensure All Services Are Running
```bash
docker-compose ps
# Should show all 11 services in "Up" status
```

### 2. Open Dashboard
Open your browser to: **http://localhost:7000**

### 3. Run Interactive Demo
```bash
# From project root
python3 demo_log_generator.py

# Or with Python environment activated
source .venv/bin/activate
python demo_log_generator.py
```

## Demo Scenarios

The interactive generator offers 7 realistic attack scenarios plus statistics viewing:

### Scenario 1: **Port Scan Detection**
- **What**: Attacker probing target for open ports
- **Pattern**: Sequential TCP packets to different ports with minimal data
- **Detection**: Isolation Forest identifies unusual traffic pattern
- **Expected**: Alert triggered for reconnaissance activity
- **Real-world**: Used by attackers to map network vulnerabilities

### Scenario 2: **DDoS (Denial of Service) Attack**
- **What**: Multiple sources flooding target server
- **Pattern**: Massive concurrent UDP floods from 5 botnet IPs
- **Detection**: Random Forest classifies as HIGH THREAT (confidence > 0.9)
- **Expected**: IP addresses blocked, alerts sent to SOC
- **Real-world**: Most common type of cyber attack

### Scenario 3: **Data Exfiltration**
- **What**: Suspicious outbound data transfer - potential data theft
- **Pattern**: Large bytes sent with unusual byte/packet ratio
- **Detection**: Anomaly detection catches high-volume outbound transfers
- **Expected**: Internal IP blocked, incident response triggered
- **Real-world**: Final stage of advanced persistent threats (APTs)

### Scenario 4: **Normal Traffic (Baseline)**
- **What**: Legitimate business operations
- **Pattern**: Web browsing, DNS queries, cloud sync, video streaming
- **Detection**: Should NOT trigger alerts (confidence < 0.3)
- **Expected**: All traffic classified as BENIGN
- **Real-world**: Validates system doesn't have false positives

### Scenario 5: **Brute Force Login Attack**
- **What**: Multiple failed authentication attempts
- **Pattern**: Rapid sequential TCP connections with small payloads
- **Detection**: Detected as attack pattern (confidence > 0.7)
- **Expected**: Account lockout triggered, login service protected
- **Real-world**: Common against SSH, RDP, and web applications

### Scenario 6: **Malware C&C Communication**
- **What**: Infected host communicating with Command & Control server
- **Pattern**: Irregular traffic with periodic check-ins and varying sizes
- **Detection**: Behavioral analysis identifies C&C signature
- **Expected**: Host quarantined, malware analysis triggered
- **Real-world**: Post-compromise persistence tactic

### Scenario 7: **Multi-Vector Attack**
- **What**: Coordinated attack with multiple threat vectors simultaneously
- **Pattern**: Combined port scan + DDoS + data exfiltration
- **Detection**: All three threats identified concurrently
- **Expected**: CRITICAL alert, manual escalation to security team
- **Real-world**: Advanced threats coordinating multiple attack types

## What to Watch on Dashboard

While running scenarios, observe the dashboard in real-time:

### **KPI Cards** (Top)
- 🔴 **High Confidence Threats**: Increases dramatically during attacks
- 🟠 **Medium Confidence**: Medium-severity anomalies
- 🟡 **Low Confidence**: Minor deviations from normal
- 📊 **Total Events**: Grows as traffic is generated
- 🚫 **Blocked IPs**: Count increases when attacks detected
- 🔔 **Alerts Sent**: Shows notification activity

### **Service Health** (Second Row)
- All 11 services should show "Healthy"
- Green checkmarks indicate normal operation

### **ML Model Status**
Shows accuracy metrics from training:
- **Isolation Forest**: Anomaly detection accuracy
- **Random Forest**: Threat classification accuracy
- Both models loaded and ready

### **Network Traffic Analysis**
Real-time visualization of flows during attacks

### **Threat Events Table** (Bottom)
Detailed log of every detected threat with:
- Source IP and Destination IP
- Confidence score
- Action taken (Block, Alert, Monitor)
- Timestamp

## Demo Flow for Presentation

### **5-Minute Demo** (Quick Impact)
```
1. Show normal baseline traffic (Scenario 4) → All BENIGN ✓
2. Run DDoS attack (Scenario 2) → CRITICAL alert ✗
3. Show blocked IPs and alerts on dashboard
4. Explain model accuracy from training
```

### **15-Minute Demo** (Full Coverage)
```
1. Baseline: Normal traffic (Scenario 4)
2. Attack 1: Port scan → Reconnaissance detected
3. Attack 2: DDoS → DoS attack blocked
4. Attack 3: Brute force → Login attempt blocked
5. Attack 4: Data exfiltration → Data theft prevented
6. Review: Show all threats on dashboard with analytics
7. Discuss: ML model accuracy and decision rules
```

### **30-Minute Deep Dive** (Full System Show)
```
1. Explain: 9-service architecture (show docker-compose diagram)
2. Walk through: Traffic capture → Feature extraction → ML detection
3. Show: Training data and model accuracy metrics
4. Run: All scenarios interactively (Scenario 9)
5. Analyze: Dashboard showing all threat events
6. Discuss: Playbook decision rules and response actions
7. Demonstrate: Hot-reload of rules without restart
8. Review: PostgreSQL threat logs with advanced filtering
```

## Command-Line Usage

### Run All Scenarios at Once
```bash
python3 demo_log_generator.py
# Select: 9 (Run All Scenarios)
# Runs all 7 scenarios back-to-back with statistics
```

### Run Single Scenario
```bash
python3 demo_log_generator.py
# Select: 2 (DDoS Attack Detection)
# Runs just the DDoS scenario with colored output
```

### View Only Statistics
```bash
python3 demo_log_generator.py
# Select: 8 (Show Stats & Logs)
# Shows current threat statistics and recent events
```

## Understanding the Output

### Color Coding
- 🟢 **GREEN**: SUCCESS - Normal operations, benign traffic
- 🟡 **YELLOW**: WARNING - Medium threat detected
- 🔴 **RED**: CRITICAL - High-priority threat detected
- 🔵 **BLUE**: INFO - Informational messages

### Traffic Event Format
```
[14:25:30] ✓ DDoS Wave 1 from 203.0.113.1: 203.0.113.1 → 192.168.1.100 (UDP) [SUCCESS]
          ✓ Event sent to capture service
          ✓ ML models analyzing traffic pattern
          ✓ Threat detected and classified
```

### Statistics Output
```
High Threats: 5          # Confidence > 0.8
Medium Threats: 3        # Confidence 0.5-0.8
Low Threats: 2           # Confidence 0.2-0.5
Total Events: 156        # Messages processed
Blocked IPs: 3           # Addresses in firewall rules
Alerts Sent: 8           # Email notifications
```

## Verification Checklist

Before running demo, verify:

```bash
# ✓ All services healthy
docker-compose ps | grep "Up"

# ✓ Dashboard accessible
curl -I http://localhost:7000

# ✓ Capture service ready
curl -I http://localhost:3001/health

# ✓ Models trained
ls -lah models/*.pkl

# ✓ Database connected
curl -s http://localhost:3006/logs | head -c 50

# ✓ Python environment
python3 -c "import requests; print('OK')"
```

## Troubleshooting

### Demo Generator Won't Connect
```bash
# Check if services are up
docker-compose ps

# Check logs of capture service
docker-compose logs traffic-capture-service

# Verify network connectivity
curl http://localhost:3001/health
```

### No Traffic Showing on Dashboard
```bash
# Check if database is receiving events
docker-compose logs threat-log-database-service

# Check database directly
docker-compose exec threat-log-database-service psql -U postgres threat_db -c "SELECT COUNT(*) FROM threat_logs;"
```

### Models Not Loaded
```bash
# Check if models exist
ls -la models/

# Check ML service logs
docker-compose logs ml-detection-service

# Restart training if needed
docker-compose restart model-training-service
```

## Performance Notes

- **Event Processing**: ~100-1000 events/second depending on system
- **Dashboard Refresh**: Real-time via WebSocket (< 1 second latency)
- **Model Inference**: < 50ms per event with scikit-learn
- **Database Insert**: Batched for throughput (1000 events/batch)

## Real Production Usage

In production, replace the demo generator with:
- **Real traffic capture** (Suricata/Zeek/pf_ring)
- **Syslog ingestion** (rsyslog/syslog-ng)
- **Cloud provider APIs** (AWS CloudTrail, Azure Monitor)
- **SIEM integration** (Splunk, ELK, Datadog)

## Demo Tips

1. **Start with baseline** (Scenario 4) to show normal pattern
2. **Build tension** by running simple attacks first (port scan)
3. **Show impact** with high-volume attacks (DDoS)
4. **Highlight prevention** by mentioning blocked IPs
5. **End with multi-vector** attack to show system resilience
6. **Ask questions** about what audience wants to see
7. **Use pauses** to let dashboard update (2-3 seconds)
8. **Take screenshots** of dashboard for presentation notes

## Security Notes

- Demo generator creates FAKE traffic - not actual network packets
- Only affects internal Docker network
- Safe to run on production dashboards (doesn't impact real traffic)
- All IPs used are not real routable addresses
- Firewall rules only affect Docker containers

## Next Steps

- Export threat logs: Dashboard → Export button
- Analyze patterns: Use PostgreSQL directly
- Create playbook rules: Edit `/playbook-decision-engine/rules/playbook-rules.json`
- Customize scenarios: Edit `demo_log_generator.py` for your use cases
- Integrate with SIEM: Add API connectors for your security tools
