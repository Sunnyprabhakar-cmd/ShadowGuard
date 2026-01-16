const express = require('express');
const nodemailer = require('nodemailer');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const app = express();
const port = 3000;

app.use(express.json());

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const configDir = process.env.ALERT_CONFIG_DIR || path.join(__dirname, 'data');
const configPath = path.join(configDir, 'alert-config.json');

function parseRecipients(value) {
  if (Array.isArray(value)) {
    return value
      .map((entry) => String(entry || '').trim())
      .filter(Boolean);
  }

  return String(value || '')
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function uniqueRecipients(recipients) {
  return [...new Set(recipients.map((entry) => entry.toLowerCase()))];
}

function validateRecipients(recipients) {
  return recipients.every((entry) => emailRegex.test(entry));
}

function getDefaultAlertConfig() {
  const envRecipients = uniqueRecipients(parseRecipients(
    process.env.ALERT_RECIPIENTS || process.env.ALERT_RECIPIENT || 'admin@shadowguard.com'
  ));

  return {
    recipients: envRecipients,
    criticalOnly: String(process.env.ALERT_CRITICAL_ONLY || 'true').toLowerCase() !== 'false',
  };
}

function loadAlertConfig() {
  const defaults = getDefaultAlertConfig();

  try {
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }

    if (!fs.existsSync(configPath)) {
      fs.writeFileSync(configPath, JSON.stringify(defaults, null, 2));
      return defaults;
    }

    const persisted = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    const recipients = uniqueRecipients(parseRecipients(persisted.recipients || defaults.recipients));

    return {
      recipients: recipients.length > 0 ? recipients : defaults.recipients,
      criticalOnly: typeof persisted.criticalOnly === 'boolean' ? persisted.criticalOnly : defaults.criticalOnly,
    };
  } catch (error) {
    console.warn('Falling back to default alert config:', error.message);
    return defaults;
  }
}

function saveAlertConfig(alertConfig) {
  if (!fs.existsSync(configDir)) {
    fs.mkdirSync(configDir, { recursive: true });
  }
  fs.writeFileSync(configPath, JSON.stringify(alertConfig, null, 2));
}

function createTransporter() {
  const host = process.env.SMTP_HOST || 'smtp.ethereal.email';
  const portValue = Number(process.env.SMTP_PORT || 587);
  const user = process.env.SMTP_USER || process.env.EMAIL_USER || 'your-ethereal-user';
  const pass = process.env.SMTP_PASS || process.env.EMAIL_PASS || 'your-ethereal-pass';

  return nodemailer.createTransport({
    host,
    port: portValue,
    secure: portValue === 465,
    auth: {
      user,
      pass
    }
  });
}

const alertConfig = loadAlertConfig();
const transporter = createTransporter();
const fromAddress = process.env.ALERT_FROM || process.env.SMTP_FROM || 'alert@shadowguard.com';
const alwaysCcSender = String(process.env.ALWAYS_CC_SENDER || 'true').toLowerCase() !== 'false';

function getEffectiveRecipients() {
  const recipients = [...alertConfig.recipients];
  if (alwaysCcSender && fromAddress && !recipients.includes(fromAddress.toLowerCase())) {
    recipients.push(fromAddress.toLowerCase());
  }
  return [...new Set(recipients)];
}

app.get('/config', (req, res) => {
  res.json({
    recipients: getEffectiveRecipients(),
    recipient: getEffectiveRecipients().join(', '),
    criticalOnly: alertConfig.criticalOnly,
  });
});

app.post('/config', (req, res) => {
  const { recipient, recipients, criticalOnly } = req.body || {};

  if (recipient !== undefined || recipients !== undefined) {
    const normalizedRecipients = uniqueRecipients(parseRecipients(
      recipients !== undefined ? recipients : recipient
    ));

    if (normalizedRecipients.length === 0 || !validateRecipients(normalizedRecipients)) {
      return res.status(400).json({ error: 'Invalid email address list' });
    }

    alertConfig.recipients = normalizedRecipients;
  }

  if (criticalOnly !== undefined) {
    alertConfig.criticalOnly = Boolean(criticalOnly);
  }

  saveAlertConfig(alertConfig);

  res.json({
    message: 'Alert settings updated',
    recipients: alertConfig.recipients,
    recipient: alertConfig.recipients.join(', '),
    criticalOnly: alertConfig.criticalOnly,
  });
});

app.post('/alert', async (req, res) => {
  const { action, details } = req.body;
  console.log('Sending alert for action:', action);

  try {
    const attackType = String(details?.attack_type || details?.attackType || '').toLowerCase();
    const isZeroDay = attackType === 'zero_day' || attackType === 'zero_day_attack';
    const isCritical = action === 'block'
      || details?.severity === 'critical'
      || details?.severity === 'high'
      || isZeroDay;
    const shouldSendEmail = alertConfig.recipients.length > 0
      && (!alertConfig.criticalOnly || isCritical || isZeroDay);

    if (shouldSendEmail) {
      try {
        const effectiveRecipients = getEffectiveRecipients();
        const mailOptions = {
          from: fromAddress,
          to: effectiveRecipients.join(', '),
          subject: isZeroDay
            ? `Zero-Day Alert: ${action}`
            : `Threat Alert: ${action}`,
          text: [
            `Action: ${action}`,
            `Severity: ${details?.severity || 'unknown'}`,
            `Attack Type: ${details?.attack_type || details?.attackType || 'unknown'}`,
            `Source IP: ${details?.sourceIp || details?.src_ip || details?.ip || 'N/A'}`,
            `Destination IP: ${details?.dst_ip || 'N/A'}`,
            `Reason: ${details?.reason || 'N/A'}`,
            '',
            `Full details: ${JSON.stringify(details)}`
          ].join('\n')
        };

        await transporter.sendMail(mailOptions);
        console.log(`Alert email sent to ${effectiveRecipients.join(', ')}`);
      } catch (emailError) {
        console.warn('Email notification failed (continuing with logging):', emailError.message);
      }
    } else {
      console.log('Email skipped: non-critical action with criticalOnly enabled');
    }

    try {
      await axios.post('http://automated-response-service:3000/respond', { action, details });
      console.log('Automated response triggered and logged');
    } catch (responseError) {
      console.error('Response service call failed:', responseError.message);
    }

    res.json({ message: 'Alert processed and response triggered' });
  } catch (error) {
    console.error('Error in alert service:', error);
    res.status(500).json({ error: 'Failed to process alert' });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(port, () => {
  console.log(`Alert Notification Service listening on port ${port}`);
});
