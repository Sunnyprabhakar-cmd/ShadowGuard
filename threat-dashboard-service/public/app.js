// Wait for React to be available
if (!window.React || !window.ReactDOM) {
  console.error('React or ReactDOM not loaded');
}

console.log('Dashboard app.js loaded, React version:', window.React?.version);

const { useState, useEffect, useRef } = React;

function Dashboard() {
  const [stats, setStats] = useState({
    total_events: 0,
    high_threats: 0,
    medium_threats: 0,
    low_threats: 0,
    blocked_ips: 0,
    alerts_sent: 0,
    monitored_flows: 0
  });
  
  const [services, setServices] = useState({});
  const [threats, setThreats] = useState([]);
  const [models, setModels] = useState({});
  const [traffic, setTraffic] = useState({});
  const [metrics, setMetrics] = useState({});
  const [refreshRate, setRefreshRate] = useState(5000);
  const [isConnected, setIsConnected] = useState(false);
  const [alertEmail, setAlertEmail] = useState('admin@shadowguard.com');
  const [criticalOnly, setCriticalOnly] = useState(true);
  const [alertConfigMessage, setAlertConfigMessage] = useState('');
  const wsRef = useRef(null);
  const dataFetchIntervalRef = useRef(null);

  const fetchAlertConfig = async () => {
    try {
      const res = await fetch('/api/alerts/config');
      if (!res.ok) return;
      const data = await res.json();
      setAlertEmail(data.recipient || (data.recipients || []).join(', ') || 'admin@shadowguard.com');
      setCriticalOnly(Boolean(data.criticalOnly));
    } catch (error) {
      console.error('Failed to fetch alert config:', error);
    }
  };

  // WebSocket connection
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    wsRef.current = new WebSocket(`${protocol}//${window.location.host}`);

    wsRef.current.onopen = () => {
      console.log('Connected to dashboard WebSocket');
      setIsConnected(true);
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'metrics_update') {
        setMetrics(data.metrics);
      }
    };

    wsRef.current.onerror = () => {
      setIsConnected(false);
    };

    wsRef.current.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // Fetch data periodically
  useEffect(() => {
    fetchAlertConfig();

    const fetchData = async () => {
      try {
        // Fetch statistics
        const statsRes = await fetch('/api/statistics');
        if (statsRes.ok) setStats(await statsRes.json());

        // Fetch service health
        const servicesRes = await fetch('/api/services/health');
        if (servicesRes.ok) setServices(await servicesRes.json());

        // Fetch threats
        const threatsRes = await fetch('/api/threats?limit=50');
        if (threatsRes.ok) {
          const data = await threatsRes.json();
          setThreats(data.logs || []);
        }

        // Fetch models
        const modelsRes = await fetch('/api/models');
        if (modelsRes.ok) setModels(await modelsRes.json());

        // Fetch traffic
        const trafficRes = await fetch('/api/traffic');
        if (trafficRes.ok) setTraffic(await trafficRes.json());
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
    dataFetchIntervalRef.current = setInterval(fetchData, refreshRate);

    return () => {
      if (dataFetchIntervalRef.current) clearInterval(dataFetchIntervalRef.current);
    };
  }, [refreshRate]);

  const saveAlertConfig = async () => {
    setAlertConfigMessage('');

    const normalized = alertEmail.trim();
    const recipients = normalized
      .split(',')
      .map((entry) => entry.trim())
      .filter(Boolean);
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!recipients.length || !recipients.every((entry) => emailRegex.test(entry))) {
      setAlertConfigMessage('Please enter valid comma-separated email addresses');
      return;
    }

    try {
      const res = await fetch('/api/alerts/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipients: normalized, criticalOnly })
      });

      const data = await res.json();
      if (!res.ok) {
        setAlertConfigMessage(data.error || 'Failed to save email settings');
        return;
      }

      setAlertEmail(data.recipient || normalized);
      setCriticalOnly(Boolean(data.criticalOnly));
      setAlertConfigMessage('Email settings saved');
    } catch (error) {
      setAlertConfigMessage('Failed to save email settings');
    }
  };

  const reloadRules = async () => {
    try {
      const res = await fetch('/api/rules/reload', { method: 'POST' });
      if (res.ok) {
        alert('Playbook rules reloaded successfully');
      }
    } catch (error) {
      alert('Failed to reload rules: ' + error.message);
    }
  };

  const exportLogs = async () => {
    try {
      const res = await fetch('/api/export/logs');
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `threat-logs-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      alert('Failed to export logs: ' + error.message);
    }
  };

  const getStatusColor = (status) => {
    return status === 'healthy' ? 'healthy' : 'unhealthy';
  };

  const getThreatColor = (confidence) => {
    if (confidence > 0.8) return 'high-threat';
    if (confidence > 0.5) return 'medium-threat';
    return 'low-threat';
  };

  const getSeverityClass = (threat) => {
    const severity = String(threat.severity || threat.details?.severity || '').toLowerCase();
    if (severity === 'critical' || severity === 'high') return 'high-threat';
    if (severity === 'medium') return 'medium-threat';
    if (severity === 'low') return 'low-threat';
    return getThreatColor(threat.confidence || 0);
  };

  const formatAttackType = (threat) => {
    const rawType = threat.attack_type || threat.attackType || threat.details?.attack_type ||
      threat.details?.attackType || threat.type || 'unknown';
    const normalizedType = String(rawType).trim();
    const labels = {
      port_scan: 'Port Scan',
      ddos: 'DDoS',
      ddos_attack: 'DDoS',
      data_exfiltration: 'Data Exfiltration',
      normal_traffic: 'Normal Traffic',
      brute_force: 'Brute Force',
      brute_force_attack: 'Brute Force',
      malware_c2: 'Malware C&C',
      malware_command_control: 'Malware C&C',
      multi_vector: 'Multi-Vector',
      zero_day: 'Zero-Day',
      zero_day_attack: 'Zero-Day',
      response: 'Response',
      unknown: 'Unknown'
    };
    const key = normalizedType.toLowerCase().replace(/\s+/g, '_');
    if (labels[key]) return labels[key];
    if (/^\d+$/.test(normalizedType)) return `Class ${normalizedType}`;
    return normalizedType
      .replace(/[_-]+/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1>🛡️ Shadow Guard Dashboard</h1>
          <div className="header-controls">
            <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
              {isConnected ? '● Live' : '○ Offline'}
            </span>
            <div className="alert-settings">
              <input
                type="text"
                value={alertEmail}
                onChange={(e) => setAlertEmail(e.target.value)}
                placeholder="alert1@example.com, alert2@example.com"
                className="alert-email-input"
              />
              <label className="critical-only-toggle">
                <input
                  type="checkbox"
                  checked={criticalOnly}
                  onChange={(e) => setCriticalOnly(e.target.checked)}
                />
                Critical only
              </label>
              <button onClick={saveAlertConfig}>Save Email</button>
            </div>
            <select value={refreshRate} onChange={(e) => setRefreshRate(Number(e.target.value))}>
              <option value={3000}>Refresh: 3s</option>
              <option value={5000}>Refresh: 5s</option>
              <option value={10000}>Refresh: 10s</option>
              <option value={30000}>Refresh: 30s</option>
            </select>
            <button onClick={reloadRules}>⚙️ Reload Rules</button>
            <button onClick={exportLogs}>📥 Export Logs</button>
          </div>
        </div>
        {alertConfigMessage && <div className="alert-config-message">{alertConfigMessage}</div>}
      </header>

      {/* Key Metrics */}
      <section className="metrics-section">
        <div className="metric-card high">
          <div className="metric-value">{stats.high_threats}</div>
          <div className="metric-label">High Threats</div>
          <div className="metric-icon">🔴</div>
        </div>
        <div className="metric-card medium">
          <div className="metric-value">{stats.medium_threats}</div>
          <div className="metric-label">Medium Threats</div>
          <div className="metric-icon">🟠</div>
        </div>
        <div className="metric-card low">
          <div className="metric-value">{stats.low_threats}</div>
          <div className="metric-label">Low Threats</div>
          <div className="metric-icon">🟡</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{stats.total_events}</div>
          <div className="metric-label">Total Events</div>
          <div className="metric-icon">📊</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{stats.blocked_ips}</div>
          <div className="metric-label">Blocked IPs</div>
          <div className="metric-icon">🚫</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{stats.alerts_sent}</div>
          <div className="metric-label">Alerts Sent</div>
          <div className="metric-icon">🔔</div>
        </div>
      </section>

      {/* Main Content */}
      <div className="dashboard-grid">
        {/* Services Health */}
        <section className="card services-card">
          <h2>Service Health</h2>
          <div className="services-list">
            {Object.entries(services).map(([name, data]) => (
              <div key={name} className={`service-item ${getStatusColor(data.status)}`}>
                <span className="service-label">{name.replace(/_/g, ' ')}</span>
                <span className={`status-badge ${data.status}`}>
                  {data.status === 'healthy' ? '✓' : '✗'} {data.status}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* ML Models Status */}
        <section className="card models-card">
          <h2>ML Models</h2>
          <div className="models-list">
            {Object.entries(models).map(([name, data]) => (
              <div key={name} className="model-item">
                <div className="model-name">{name.replace(/_/g, ' ')}</div>
                <div className="model-status">
                  <span className="status-badge trained">✓ {data.status}</span>
                  <span className="model-size">{data.size}</span>
                </div>
                <div className="model-details">
                  Trained on {data.samples_trained} samples
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Traffic Analysis */}
        <section className="card traffic-card">
          <h2>Network Traffic</h2>
          <div className="traffic-stats">
            <div className="traffic-stat">
              <span className="label">Total Flows</span>
              <span className="value">{traffic.total_flows || 0}</span>
            </div>
            <div className="traffic-stat">
              <span className="label">Avg Duration</span>
              <span className="value">{(traffic.avg_duration || 0).toFixed(2)}s</span>
            </div>
            <div className="traffic-stat">
              <span className="label">Avg Bytes Sent</span>
              <span className="value">{(traffic.avg_bytes_sent || 0).toLocaleString()}</span>
            </div>
          </div>
          <div className="protocols">
            <h3>By Protocol</h3>
            {traffic.by_protocol && Object.entries(traffic.by_protocol).map(([proto, count]) => (
              <div key={proto} className="protocol-item">
                <span>{proto.toUpperCase()}</span>
                <span className="count">{count}</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Recent Threats */}
      <section className="card threats-card">
        <h2>Recent Threat Events (Last 50)</h2>
        <div className="threats-table">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Source IP</th>
                <th>Destination IP</th>
                <th>Type of Attack</th>
                <th>Severity</th>
                <th>Confidence</th>
                <th>Action</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {threats.length === 0 ? (
                <tr><td colSpan="8" className="empty">No threat events</td></tr>
              ) : (
                threats.map((threat, idx) => (
                  <tr key={idx} className={getSeverityClass(threat)}>
                    <td>{new Date(threat.timestamp).toLocaleString()}</td>
                    <td className="ip">{threat.src_ip || 'N/A'}</td>
                    <td className="ip">{threat.dst_ip || 'N/A'}</td>
                    <td><span className="attack-type">{formatAttackType(threat)}</span></td>
                    <td className="action">{threat.severity || threat.details?.severity || 'N/A'}</td>
                    <td className="confidence">{(threat.confidence || 0).toFixed(2)}</td>
                    <td className="action">{threat.action || 'N/A'}</td>
                    <td className="status">
                      {threat.action === 'block' ? '🚫' : threat.action === 'alert' ? '🔔' : '👁️'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <p>Shadow Guard - Real-time Threat Detection & Response System</p>
        <p>Last updated: {new Date().toLocaleTimeString()}</p>
      </footer>
    </div>
  );
}

// Render when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(React.createElement(Dashboard));
  });
} else {
  const root = ReactDOM.createRoot(document.getElementById('root'));
  root.render(React.createElement(Dashboard));
}
