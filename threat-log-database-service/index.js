const express = require('express');
const { Pool } = require('pg');
const app = express();
const port = 3000;

app.use(express.json());

const pool = new Pool({
  user: 'user',
  host: 'postgres',
  database: 'threat_logs',
  password: 'password',
  port: 5432,
});

app.post('/log', async (req, res) => {
  const logData = req.body;
  try {
    const query = `
      INSERT INTO threat_logs (type, action, details, timestamp)
      VALUES ($1, $2, $3, COALESCE($4::timestamp, NOW()))
    `;
    await pool.query(query, [
      logData.type || 'unknown',
      logData.action || 'monitor',
      JSON.stringify(logData.details || {}),
      logData.timestamp || null,
    ]);
    res.json({ message: 'Log saved' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to save log' });
  }
});

app.get('/logs', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM threat_logs ORDER BY timestamp DESC');

    const normalizedLogs = result.rows.map((row) => {
      const details = row.details || {};
      const probabilities = Array.isArray(details.probabilities) ? details.probabilities : [];
      const explicitConfidence = typeof details.confidence === 'number' ? details.confidence : null;
      const confidence = explicitConfidence !== null
        ? explicitConfidence
        : (probabilities.length > 0 ? Math.max(...probabilities) : 0);

      return {
        id: row.id,
        type: row.type,
        attack_type: details.attack_type || details.attackType || row.type,
        action: row.action,
        severity: details.severity || null,
        timestamp: row.timestamp,
        confidence,
        src_ip: details.sourceIp || details.src_ip || null,
        dst_ip: details.dst_ip || null,
        protocol: details.protocol || null,
        bytes_sent: details.bytes_sent || details.bytesSent || 0,
        duration: details.duration || 0,
        details,
      };
    });

    res.json(normalizedLogs);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch logs' });
  }
});

app.post('/logs/reset', async (req, res) => {
  try {
    await pool.query('TRUNCATE TABLE threat_logs RESTART IDENTITY');
    res.json({ message: 'Threat logs reset' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to reset logs' });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(port, () => {
  console.log(`Threat Log Database Service listening on port ${port}`);
});
