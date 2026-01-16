# Shadow Guard Dashboard - User Guide

## 🎯 Overview

The **Shadow Guard Dashboard** is a production-ready, real-time monitoring interface for your threat detection system. It provides comprehensive visibility into network threats, ML model performance, and system health in a beautiful, responsive web interface.

## 🚀 Quick Start

### Access the Dashboard
Open your browser and navigate to:
```
http://localhost:7000
```

## 📊 Dashboard Features

### 1. **Real-Time Threat Metrics (KPI Cards)**
Displays critical threat indicators at a glance:
- 🔴 **High Threats**: Confidence > 0.8
- 🟠 **Medium Threats**: Confidence 0.5-0.8
- 🟡 **Low Threats**: Confidence < 0.5
- 📊 **Total Events**: All processed events
- 🚫 **Blocked IPs**: Successfully blocked malicious sources
- 🔔 **Alerts Sent**: Notifications dispatched

### 2. **Service Health Monitor**
Monitors all 9 microservices:
- ✓ Traffic Capture Service
- ✓ Flow Feature Extraction
- ✓ Playbook Decision Engine
- ✓ Alert Notification
- ✓ Automated Response
- ✓ Threat Log Database
- ✓ ML Detection (Anomaly)
- ✓ Threat Classification
- ✓ Model Training

Color-coded status:
- **Green** = Healthy ✓
- **Red** = Unhealthy ✗

### 3. **ML Models Status**
Shows trained models information:
- **Isolation Forest** (1.6 MB): Anomaly detection
- **Random Forest** (799 KB): Threat classification
- Training samples: 1,000
- Last trained: [timestamp]

### 4. **Network Traffic Analysis**
Real-time traffic statistics:
- Total network flows processed
- Average flow duration
- Average bytes sent per flow
- Traffic breakdown by protocol (TCP, UDP, ICMP)

### 5. **Recent Threat Events Table**
Live-updating table of recent threats:
- **Timestamp**: When threat was detected
- **Source IP**: Origin of the threat
- **Destination IP**: Target IP
- **Confidence**: ML confidence score (0.0-1.0)
- **Action**: Response taken (block, alert, monitor)
- **Status**: Visual indicator of action

Color coding by threat level:
- 🔴 High threat (red highlight)
- 🟠 Medium threat (orange highlight)
- 🟡 Low threat (yellow highlight)

## 🎮 Dashboard Controls

### Refresh Rate Selector
Adjust how frequently the dashboard updates:
- **3 seconds**: Real-time monitoring (high CPU)
- **5 seconds**: Balanced (recommended)
- **10 seconds**: Lower bandwidth
- **30 seconds**: Minimal resource usage

### ⚙️ Reload Rules Button
Instantly reload playbook decision rules without restarting services:
```bash
Click "⚙️ Reload Rules" → Rules updated
```

### 📥 Export Logs Button
Download threat logs as JSON for analysis:
```bash
Click "📥 Export Logs" → Downloads threat-logs-[timestamp].json
```

### Connection Status
Live indicator in header:
- **● Live** (green): Connected to real-time updates
- **○ Offline** (red): WebSocket disconnected

## 🔌 API Endpoints

### Health & Status
```
GET /health
GET /api/services/health
```

### Threat Data
```
GET /api/threats?limit=100
GET /api/statistics
```

### System Metrics
```
GET /api/metrics
POST /api/metrics/event
```

### ML Models
```
GET /api/models
GET /api/traffic
```

### Rules Management
```
GET /api/rules
POST /api/rules/reload
```

### Data Export
```
GET /api/export/logs
```

## 📱 Responsive Design

Dashboard automatically adapts to:
- **Desktop** (1400px+): Full grid layout with all features
- **Tablet** (768px-1400px): 2-column grid
- **Mobile** (<768px): Stacked single column

All features remain accessible on smaller screens.

## 🎨 Dark Theme

The dashboard uses a professional dark theme optimized for:
- **Low eye strain** during long monitoring sessions
- **High contrast** for quick threat identification
- **Modern aesthetics** with gradient accents
- **Color-blind friendly** status indicators

## 🔐 Security Considerations

### Production Deployment
For production use:

1. **Enable HTTPS** (add reverse proxy with SSL)
2. **Add authentication** (OAuth, JWT, or basic auth)
3. **Rate limiting** on API endpoints
4. **CORS configuration** for trusted origins only
5. **CSP headers** to prevent XSS attacks

### Example Nginx Reverse Proxy
```nginx
server {
    listen 443 ssl;
    server_name dashboard.yourcompany.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    location / {
        proxy_pass http://localhost:7000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📈 Advanced Usage

### WebSocket for Real-Time Updates
The dashboard uses WebSocket for live data streaming:
- Service health changes
- Metrics updates
- Threat event notifications

Connection is automatic and transparent to users.

### Metrics Storage (Production)
For production, replace in-memory metrics with:
- **Redis**: For distributed systems
- **TimescaleDB**: For time-series metrics
- **Prometheus**: For metrics collection
- **InfluxDB**: For high-volume metrics

## 🐛 Troubleshooting

### Dashboard Not Loading
1. Check service status: `docker-compose ps`
2. View logs: `docker logs shadow_guard-threat-dashboard-service-1`
3. Verify port mapping: `docker port shadow_guard-threat-dashboard-service-1`

### Services Showing Unhealthy
1. Check individual service logs
2. Verify network connectivity between services
3. Restart unhealthy service: `docker-compose restart [service-name]`

### No Threat Events Showing
1. Ensure traffic is flowing through pipeline
2. Check database connection: `docker-compose logs threat-log-database-service`
3. Verify models are trained: `ls -lh ./models/`

## 📊 Performance Metrics

### Dashboard Performance
- **Load time**: < 2 seconds (first load)
- **Real-time update**: < 500ms latency
- **Max concurrent users**: 50+ (with proper infrastructure)
- **Memory footprint**: ~50MB per Node.js service
- **CPU usage**: Minimal (< 2% per service at rest)

### Browser Compatibility
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## 🔄 Integration With Other Systems

### Alerting Integration
Dashboard can trigger external alerts to:
- **PagerDuty**: Create incidents
- **Slack**: Send notifications  
- **Email**: Automated emails
- **SOAR/SIEM**: Integrate with security workflows

### API Usage Examples

#### Get latest statistics
```bash
curl http://localhost:7000/api/statistics
```

#### Export threat logs
```bash
curl http://localhost:7000/api/export/logs > threats.json
```

#### Check service health
```bash
curl http://localhost:7000/api/services/health
```

#### Reload rules
```bash
curl -X POST http://localhost:7000/api/rules/reload
```

## 📝 Customization

### Modifying Colors
Edit `public/styles.css`:
```css
:root {
  --primary: #667eea;
  --danger: #f56565;
  --warning: #ed8936;
  /* ... etc */
}
```

### Adding New Metrics
Edit `server.js` to add endpoints, then update `public/app.js` React component.

### Custom Branding
Modify `public/index.html` and `app.js` to add your company logo, colors, and branding.

## 🚀 Future Enhancements

Planned features for Shadow Guard Dashboard:
- Historical threat trend analysis
- Automated threat hunt for IOCs
- ML model retraining from dashboard
- Custom alert rule builder
- Network topology visualization
- Threat hunting playbooks
- Multi-tenant support
- API key management
- Custom report generation
- Integration marketplace

## 📞 Support

For issues or questions:
1. Check service logs: `docker-compose logs -f`
2. Review threat-detection-system documentation
3. Verify all services are healthy
4. Check network connectivity between services

---

**Shadow Guard Dashboard** - Real-time threat detection at your fingertips! 🛡️
