const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const axios = require('axios');
const path = require('path');
const ws = require('ws');
const http = require('http');

const app = express();
const server = http.createServer(app);
const wss = new ws.Server({ server });

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static('public'));

// Configuration
const SERVICE_URLS = {
  traffic_capture: 'http://traffic-capture-service:3000',
  feature_extraction: 'http://flow-feature-extraction-service:3000',
  ml_detection: 'http://ml-detection-service:8000',
  classification: 'http://threat-classification-service:8000',
  decision_engine: 'http://playbook-decision-engine:3000',
  alert: 'http://alert-notification-service:3000',
  response: 'http://automated-response-service:3000',
  database: 'http://threat-log-database-service:3000',
  training: 'http://model-training-service:8000'
};

// In-memory metrics storage (production: use Redis/TimescaleDB)
const metrics = {
  events_processed: 0,
  threats_detected: 0,
  alerts_sent: 0,
  responses_executed: 0,
  last_update: Date.now(),
  active_connections: 0
};

// WebSocket broadcast function
function broadcast(data) {
  wss.clients.forEach(client => {
    if (client.readyState === ws.OPEN) {
      client.send(JSON.stringify(data));
    }
  });
}

// WebSocket connection handler
wss.on('connection', (ws) => {
  metrics.active_connections = wss.clients.size;
  broadcast({ type: 'connection', active_connections: metrics.active_connections });
  
  ws.on('close', () => {
    metrics.active_connections = wss.clients.size;
    broadcast({ type: 'connection', active_connections: metrics.active_connections });
  });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: Date.now(),
    uptime: process.uptime(),
    active_connections: metrics.active_connections
  });
});

// Get all service health status
app.get('/api/services/health', async (req, res) => {
  const health = {};
  
  for (const [name, url] of Object.entries(SERVICE_URLS)) {
    try {
      const response = await axios.get(`${url}/health`, { timeout: 3000 });
      health[name] = {
        status: 'healthy',
        response_time: response.headers['x-response-time'] || null,
        timestamp: Date.now()
      };
    } catch (error) {
      health[name] = {
        status: 'unhealthy',
        error: error.message,
        timestamp: Date.now()
      };
    }
  }
  
  res.json(health);
});

// Get threat logs
app.get('/api/threats', async (req, res) => {
  try {
    const limit = req.query.limit || 100;
    const response = await axios.get(
      `${SERVICE_URLS.database}/logs`,
      { timeout: 5000 }
    );
    const logs = Array.isArray(response.data) ? response.data : [];
    res.json({
      total: logs.length,
      logs: logs.slice(0, limit)
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch threat logs' });
  }
});

// Get threat statistics
app.get('/api/statistics', async (req, res) => {
  try {
    const logsResponse = await axios.get(`${SERVICE_URLS.database}/logs`);
    const logs = Array.isArray(logsResponse.data) ? logsResponse.data : [];
    const severityOf = (log) => {
      const severity = String(log.severity || log.details?.severity || '').toLowerCase();
      if (severity === 'critical' || severity === 'high') return 'high';
      if (severity === 'medium') return 'medium';
      if (severity === 'low') return 'low';
      if (log.confidence > 0.8) return 'high';
      if (log.confidence > 0.5) return 'medium';
      return 'low';
    };
    
    const stats = {
      total_events: logs.length,
      high_threats: logs.filter(l => severityOf(l) === 'high').length,
      medium_threats: logs.filter(l => severityOf(l) === 'medium').length,
      low_threats: logs.filter(l => severityOf(l) === 'low').length,
      blocked_ips: logs.filter(l => l.action === 'block').length,
      alerts_sent: logs.filter(l => l.action === 'alert' || l.action === 'block').length,
      monitored_flows: logs.filter(l => l.action === 'monitor').length
    };
    
    res.json(stats);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch statistics' });
  }
});

// Get real-time metrics
app.get('/api/metrics', (req, res) => {
  res.json({
    ...metrics,
    timestamp: Date.now()
  });
});

// Update metrics (called by other services)
app.post('/api/metrics/event', (req, res) => {
  const { type } = req.body;
  
  if (type === 'event_processed') metrics.events_processed++;
  else if (type === 'threat_detected') metrics.threats_detected++;
  else if (type === 'alert_sent') metrics.alerts_sent++;
  else if (type === 'response_executed') metrics.responses_executed++;
  
  metrics.last_update = Date.now();
  
  broadcast({
    type: 'metrics_update',
    metrics: metrics
  });
  
  res.json({ success: true });
});

// Get models status
app.get('/api/models', async (req, res) => {
  try {
    const response = await axios.get(`${SERVICE_URLS.training}/health`);
    res.json({
      isolation_forest: {
        status: 'trained',
        size: '1.6 MB',
        accuracy: 'N/A',
        samples_trained: 1000
      },
      random_forest: {
        status: 'trained',
        size: '799 KB',
        accuracy: 'N/A',
        samples_trained: 1000
      }
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch model status' });
  }
});

// Get network traffic analysis
app.get('/api/traffic', async (req, res) => {
  try {
    const logsResponse = await axios.get(`${SERVICE_URLS.database}/logs`);
    const logs = Array.isArray(logsResponse.data) ? logsResponse.data : [];
    
    const protocolStats = {};
    logs.forEach(log => {
      const proto = log.protocol || 'unknown';
      protocolStats[proto] = (protocolStats[proto] || 0) + 1;
    });
    
    res.json({
      total_flows: logs.length,
      by_protocol: protocolStats,
      avg_bytes_sent: logs.length > 0 ? 
        logs.reduce((sum, l) => sum + (l.bytes_sent || 0), 0) / logs.length : 0,
      avg_duration: logs.length > 0 ?
        logs.reduce((sum, l) => sum + (l.duration || 0), 0) / logs.length : 0
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch traffic data' });
  }
});

// Reload playbook rules endpoint
app.post('/api/rules/reload', async (req, res) => {
  try {
    const response = await axios.post(`${SERVICE_URLS.decision_engine}/reload-rules`);
    res.json({ success: true, message: 'Rules reloaded successfully' });
  } catch (error) {
    res.status(500).json({ error: 'Failed to reload rules' });
  }
});

// Get current playbook rules
app.get('/api/rules', async (req, res) => {
  try {
    // Return sample rules structure
    res.json({
      benign: {
        confidence_threshold: 0.3,
        action: 'monitor',
        description: 'Monitor normal traffic'
      },
      medium_threat: {
        confidence_threshold: 0.5,
        action: 'alert',
        description: 'Send alert for medium confidence threats'
      },
      high_threat: {
        confidence_threshold: 0.8,
        action: 'block',
        description: 'Block high confidence threats'
      },
      zero_day: {
        confidence_threshold: 0.95,
        action: 'block',
        description: 'Escalate zero-day style attacks immediately'
      }
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch rules' });
  }
});

// Get alert notification configuration
app.get('/api/alerts/config', async (req, res) => {
  try {
    const response = await axios.get(`${SERVICE_URLS.alert}/config`, { timeout: 5000 });
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch alert config' });
  }
});

// Update alert notification configuration
app.post('/api/alerts/config', async (req, res) => {
  try {
    const response = await axios.post(`${SERVICE_URLS.alert}/config`, req.body, { timeout: 5000 });
    res.json(response.data);
  } catch (error) {
    const status = error.response?.status || 500;
    const payload = error.response?.data || { error: 'Failed to update alert config' };
    res.status(status).json(payload);
  }
});

// Export data as JSON
app.get('/api/export/logs', async (req, res) => {
  try {
    const logsResponse = await axios.get(`${SERVICE_URLS.database}/logs`);
    const logs = Array.isArray(logsResponse.data) ? logsResponse.data : [];
    
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Content-Disposition', 'attachment; filename=threat-logs.json');
    res.json(logs);
  } catch (error) {
    res.status(500).json({ error: 'Failed to export logs' });
  }
});

// Serve dashboard frontend
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

// Error handler
app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
const PORT = process.env.PORT || 3000;
server.listen(PORT, '0.0.0.0', () => {
  console.log(`[dashboard] Listening on port ${PORT}`);
  console.log(`[dashboard] Dashboard available at http://localhost:${PORT}`);
});

// Periodic health check (every 30 seconds)
setInterval(async () => {
  for (const [name, url] of Object.entries(SERVICE_URLS)) {
    try {
      await axios.get(`${url}/health`, { timeout: 2000 });
    } catch (error) {
      // Service unhealthy, could log or alert
    }
  }
}, 30000);
