# 🎯 Shadow Guard Demo - Quick Reference Card

## 🚀 Quick Start (2 minutes)

```bash
# Terminal 1: Start all services
./start_demo.sh
# OR
docker-compose up -d

# Terminal 2: Open dashboard
http://localhost:7000

# Terminal 3: Run demo generator
python3 demo_log_generator.py
```

---

## 📊 What You'll See on Dashboard

### Top Row - KPI Cards
```
┌─────────────────┬──────────────────┬─────────────────┐
│ 🔴 HIGH: 5      │ 🟠 MEDIUM: 3     │ 🟡 LOW: 2       │
│ High confidence │ Medium severity  │ Minor alerts    │
│ threats detected│ anomalies        │ or deviations   │
└─────────────────┴──────────────────┴─────────────────┘

┌────────────────┬─────────────────┬──────────────────┐
│ 📊 Events: 156 │ 🚫 Blocked: 3   │ 🔔 Alerts: 8     │
│ Total traffic  │ IP addresses    │ Notifications    │
│ events         │ in firewall     │ sent to SOC      │
└────────────────┴─────────────────┴──────────────────┘
```

### Service Health
```
✓ Traffic Capture (3001)        [Healthy]
✓ Feature Extraction (3002)     [Healthy]
✓ ML Detection (8001)            [Healthy]
✓ Classification (8002)          [Healthy]
✓ Decision Engine (3003)         [Healthy]
✓ Alert Service (3004)           [Healthy]
✓ Response Service (3005)        [Healthy]
✓ Database (3006 + 5433)         [Healthy]
✓ Model Training (8003)          [Healthy]
✓ Dashboard (7000)               [Healthy]
```

### ML Model Status
```
Isolation Forest                 Trained ✓
  Accuracy: XX.X%
  Last trained: Today
  Status: Ready for inference

Random Forest                     Trained ✓
  Accuracy: XX.X%
  Last trained: Today
  Status: Ready for inference
```

### Threat Events (Live Table)
```
SRC IP          DST IP          CONFIDENCE  ACTION      TIME
203.0.113.1 →   192.168.1.100   0.95        🚫 BLOCK   14:25:30
10.0.0.50   →   192.168.1.100   0.75        🔔 ALERT   14:25:21
192.168.1.50 →  198.51.100.23   0.88        🔔 ALERT   14:25:12
192.168.1.10 →  8.8.8.8         0.08        ✓ ALLOW    14:25:03
```

---

## 🎬 Demo Generator Menu

```
Available Scenarios:
  1. Port Scan Detection
  2. DDoS Attack Detection  ⭐ Most Impressive
  3. Data Exfiltration
  4. Normal Traffic (Baseline)
  5. Brute Force Attack
  6. Malware C&C Detection
  7. Multi-Vector Attack   ⭐ Most Impactful
  8. Show Stats & Logs
  9. Run All Scenarios
  0. Exit

Select scenario (0-9):
```

---

## ⏱️ Recommended Demo Flow (10 minutes)

### Timeline

**00:00-01:00** - Introduction
- Explain Shadow Guard architecture (9 services)
- Point out dashboard components
- Highlight ML models and playbook rules

**01:00-02:00** - Baseline (Scenario 4)
```bash
Select: 4 (Normal Traffic)
```
✅ Watch: All traffic stays GREEN/BENIGN
✅ Message: "See? Normal traffic is safe"

**02:00-04:00** - DDoS Attack (Scenario 2)
```bash
Select: 2 (DDoS Attack Detection)
```
🎯 Watch: 
  • Massive spike in traffic volume
  • 🔴 Cards turn RED - High Threat detected
  • Blocked IPs increase (3+)
  • Alerts sent instantly
✅ Message: "Real-time threat detection in action!"

**04:00-06:00** - Exfiltration (Scenario 3)
```bash
Select: 3 (Data Exfiltration)
```
🎯 Watch:
  • Unusual byte/packet ratio
  • Internal IP flagged as suspicious
  • Response engine blocks outbound
✅ Message: "Data theft prevented!"

**06:00-08:00** - Multi-Vector (Scenario 7)
```bash
Select: 7 (Multi-Vector Attack)
```
🎯 Watch:
  • 3 simultaneous attacks
  • All detected concurrently
  • Multiple IPs blocked
✅ Message: "Advanced threats detected together"

**08:00-10:00** - Q&A
- Show statistics (Option 8)
- Explain model accuracy
- Discuss playbook rules
- Demo API integration

---

## 🎨 Color Meanings

| Color | Threat Level | Confidence | Action |
|-------|-------------|-----------|--------|
| 🟢 Green | None/Benign | < 0.3 | ✅ Allow |
| 🟡 Yellow | Low | 0.3-0.5 | 👁️ Monitor |
| 🟠 Orange | Medium | 0.5-0.8 | 🔔 Alert |
| 🔴 Red | High/Critical | > 0.8 | 🚫 Block |

---

## 🔑 Key Statistics to Call Out

- **DDoS**: 5,000+ packets/second → Instantly detected
- **Port Scan**: 6 ports probed → Reconnaissance blocked
- **Data Theft**: 50MB+ exfil attempt → Stopped
- **Brute Force**: 8 login attempts → Account protected
- **Multi-Vector**: 3 threats → All detected & blocked
- **False Positives**: Normal traffic → 0% alerts

---

## 💡 Presentation Tips

1. **Start Simple**: Show baseline first (builds confidence)
2. **Build Drama**: Port scan → DDoS → Exfil (escalating severity)
3. **Pause for Effect**: Let dashboard update (2-3 sec) between scenarios
4. **Narrate**: Explain what's happening while running
5. **Ask Questions**: "What would happen if we didn't have this?"
6. **Show Impact**: Point to blocked IPs and alerts
7. **End Big**: Multi-vector attack shows system resilience
8. **Offer Customization**: "We can simulate any attack you face"

---

## 🛠️ Troubleshooting During Demo

### Services Won't Start
```bash
# Check if ports are free
lsof -i :3001 :7000 :3006 :5433

# View service logs
docker-compose logs threat-dashboard-service
```

### Dashboard Shows No Data
```bash
# Wait 10+ seconds for services
sleep 10
docker-compose ps  # Should show all "Up"

# Manually send test event
curl -X POST http://localhost:3001/capture \
  -H "Content-Type: application/json" \
  -d '{"packets": 100, "bytes": 5000, "duration": 1}'
```

### Traffic Events Not Appearing
```bash
# Check database connectivity
docker-compose logs threat-log-database-service

# Check database directly
docker-compose exec threat-log-database-service \
  psql -U postgres threat_db -c "SELECT COUNT(*) FROM threat_logs;"
```

### Generator Won't Connect
```bash
# Verify services are up
docker-compose ps

# Test capture endpoint
curl http://localhost:3001/health
```

---

## 📊 Expected Metrics (After Full Demo)

```
Total Events Generated:     ~156
Port Scan Alerts:           6
DDoS Alerts:               15
Exfiltration Alerts:        3
Brute Force Alerts:         8
C&C Alerts:                 4
Multi-Vector Alerts:        3
Normal Traffic Events:      50
---
Total High Confidence:      15
Total Medium Confidence:    12
Total Low Confidence:       5
Blocked IPs:                5-7
Alerts Sent:                8-10
False Positives:            0 ✅
```

---

## 🎓 What This Demonstrates

✅ Real-time threat detection
✅ Multiple attack vectors recognized
✅ Automated response capability
✅ ML accuracy (both RF and IF models)
✅ Zero false positives on benign traffic
✅ Scalable microservices architecture
✅ Enterprise-grade dashboard
✅ Full audit trail in database
✅ Production-ready deployment
✅ Customizable playbook rules

---

## 📞 Support

**For more details:** See `DEMO.md` in project root

**For architecture:** See `README.md`

**For dashboard features:** See `DASHBOARD.md`
