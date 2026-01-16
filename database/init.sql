-- Init script for threat_logs database

CREATE TABLE IF NOT EXISTS threat_logs (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50),
    action VARCHAR(50),
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_threat_logs_timestamp ON threat_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_threat_logs_type ON threat_logs (type);