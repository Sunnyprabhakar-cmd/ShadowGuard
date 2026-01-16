const express = require('express');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const app = express();
const port = 3000;

app.use(express.json());

const rulesPath = process.env.PLAYBOOK_RULES_PATH || path.join(__dirname, 'rules', 'playbook-rules.json');
let playbookRules = {
  benignPrediction: 0,
  confidenceThresholds: {
    low: 0.6,
    high: 0.85
  },
  actions: {
    benign: 'monitor',
    lowConfidenceThreat: 'alert',
    highConfidenceThreat: 'block'
  }
};

const highRiskAttackTypes = new Set([
  'ddos',
  'data_exfiltration',
  'malware_command_control',
  'malware_c2',
  'multi_vector',
  'zero_day',
  'zero_day_attack'
]);

const mediumRiskAttackTypes = new Set([
  'port_scan',
  'brute_force'
]);

function normalizeAttackType(value) {
  return String(value || 'unknown').trim().toLowerCase().replace(/\s+/g, '_');
}

function loadRules() {
  try {
    const raw = fs.readFileSync(rulesPath, 'utf8');
    const parsed = JSON.parse(raw);
    playbookRules = {
      ...playbookRules,
      ...parsed,
      confidenceThresholds: {
        ...playbookRules.confidenceThresholds,
        ...(parsed.confidenceThresholds || {})
      },
      actions: {
        ...playbookRules.actions,
        ...(parsed.actions || {})
      }
    };
    console.log('Playbook rules loaded from file');
  } catch (error) {
    console.warn('Using default playbook rules. Reason:', error.message);
  }
}

function decideAction(prediction, probabilities) {
  const benignPrediction = playbookRules.benignPrediction;
  const isBenign = prediction === benignPrediction;
  const maxProbability = Array.isArray(probabilities) && probabilities.length > 0
    ? Math.max(...probabilities)
    : 0;

  if (isBenign) {
    return {
      action: playbookRules.actions.benign,
      reason: 'Benign class predicted'
    };
  }

  if (maxProbability >= playbookRules.confidenceThresholds.high) {
    return {
      action: playbookRules.actions.highConfidenceThreat,
      reason: `Threat confidence high (${maxProbability.toFixed(3)})`
    };
  }

  if (maxProbability >= playbookRules.confidenceThresholds.low) {
    return {
      action: playbookRules.actions.lowConfidenceThreat,
      reason: `Threat confidence medium (${maxProbability.toFixed(3)})`
    };
  }

  return {
    action: 'manual-review',
    reason: `Threat confidence below low threshold (${maxProbability.toFixed(3)})`
  };
}

function deriveRiskMetadata(context = {}, probabilities = []) {
  const attackType = normalizeAttackType(
    context.attack_type || context.attackType || context.type || 'unknown'
  );
  const maxProbability = Array.isArray(probabilities) && probabilities.length > 0
    ? Math.max(...probabilities)
    : 0;
  const packets = Number(context.packets || 0);
  const bytesSent = Number(context.bytes_sent || context.bytesSent || 0);
  const flowType = String(context.flow_type || '').toLowerCase();
  const anomalyBoost = flowType === 'anomaly' ? 0.15 : 0;
  const volumetricBoost = packets >= 5000 || bytesSent >= 5000000 ? 0.1 : 0;

  let severity = 'low';
  let recommendedAction = playbookRules.actions.benign;
  let riskScore = Math.max(maxProbability, 0);
  let reason = `Model confidence ${maxProbability.toFixed(3)}`;

  if (attackType === 'normal_traffic' || attackType === 'benign') {
    severity = 'low';
    recommendedAction = playbookRules.actions.benign;
    riskScore = 0.1;
    reason = 'Benign traffic pattern';
  } else if (attackType === 'zero_day' || attackType === 'zero_day_attack') {
    severity = 'critical';
    recommendedAction = playbookRules.actions.highConfidenceThreat;
    riskScore = Math.max(riskScore, 0.99);
    reason = 'Zero-day scenario detected';
  } else if (highRiskAttackTypes.has(attackType)) {
    severity = 'high';
    recommendedAction = playbookRules.actions.highConfidenceThreat;
    riskScore = Math.max(riskScore, 0.9 + anomalyBoost + volumetricBoost);
    reason = `High-risk attack pattern detected (${attackType})`;
  } else if (mediumRiskAttackTypes.has(attackType)) {
    severity = 'medium';
    recommendedAction = playbookRules.actions.lowConfidenceThreat;
    riskScore = Math.max(riskScore, 0.7 + anomalyBoost);
    reason = `Medium-risk attack pattern detected (${attackType})`;
  } else if (flowType === 'anomaly' && maxProbability >= playbookRules.confidenceThresholds.high) {
    severity = 'high';
    recommendedAction = playbookRules.actions.highConfidenceThreat;
    riskScore = Math.max(riskScore, 0.9);
    reason = `Anomalous flow with high confidence (${maxProbability.toFixed(3)})`;
  } else if (flowType === 'anomaly' && maxProbability >= playbookRules.confidenceThresholds.low) {
    severity = 'medium';
    recommendedAction = playbookRules.actions.lowConfidenceThreat;
    riskScore = Math.max(riskScore, 0.7);
    reason = `Anomalous flow with medium confidence (${maxProbability.toFixed(3)})`;
  } else if (maxProbability >= playbookRules.confidenceThresholds.high) {
    severity = 'high';
    recommendedAction = playbookRules.actions.highConfidenceThreat;
    riskScore = Math.max(riskScore, 0.86);
    reason = `Threat confidence high (${maxProbability.toFixed(3)})`;
  } else if (maxProbability >= playbookRules.confidenceThresholds.low) {
    severity = 'medium';
    recommendedAction = playbookRules.actions.lowConfidenceThreat;
    riskScore = Math.max(riskScore, 0.65);
    reason = `Threat confidence medium (${maxProbability.toFixed(3)})`;
  }

  return {
    attackType,
    severity,
    riskScore: Math.min(riskScore, 0.99),
    recommendedAction,
    reason
  };
}

loadRules();

app.post('/decide', async (req, res) => {
  const { prediction, probabilities, sourceIp, context = {} } = req.body;
  console.log('Making decision for prediction:', prediction);

  try {
    const trafficContext = context || {};
    const normalizedSourceIp = sourceIp || trafficContext.src_ip || trafficContext.sourceIp || null;
    const attackType = trafficContext.attack_type || trafficContext.attackType || trafficContext.type || `class_${prediction}`;
    const risk = deriveRiskMetadata(trafficContext, probabilities);
    const modelDecision = decideAction(prediction, probabilities);
    const shouldTrustBenignPrediction = prediction === playbookRules.benignPrediction
      && (risk.attackType === 'normal_traffic' || risk.attackType === 'unknown')
      && String(trafficContext.flow_type || '').toLowerCase() !== 'anomaly';

    const selectedAction = shouldTrustBenignPrediction
      ? modelDecision.action
      : risk.recommendedAction;
    const selectedReason = shouldTrustBenignPrediction
      ? modelDecision.reason
      : risk.reason;
    const selectedSeverity = shouldTrustBenignPrediction ? 'low' : risk.severity;
    const selectedConfidence = shouldTrustBenignPrediction ? 0.1 : risk.riskScore;

    const decision = {
      action: selectedAction,
      details: {
        prediction,
        probabilities,
        confidence: selectedConfidence,
        severity: selectedSeverity,
        sourceIp: normalizedSourceIp,
        ip: normalizedSourceIp,
        src_ip: normalizedSourceIp,
        dst_ip: trafficContext.dst_ip || trafficContext.destinationIp || null,
        protocol: trafficContext.protocol || null,
        attack_type: attackType,
        packets: trafficContext.packets || 0,
        bytes_sent: trafficContext.bytes_sent || trafficContext.bytesSent || 0,
        duration: trafficContext.duration || 0,
        flow_type: trafficContext.flow_type || null,
        reason: selectedReason,
        decidedAt: new Date().toISOString()
      }
    };

    await axios.post('http://alert-notification-service:3000/alert', decision);
    console.log('Alert triggered');

    res.json(decision);
  } catch (error) {
    console.error('Error in decision engine:', error);
    res.status(500).json({ error: 'Failed to make decision' });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.post('/reload-rules', (req, res) => {
  loadRules();
  res.json({ message: 'Playbook rules reloaded' });
});

app.listen(port, () => {
  console.log(`Playbook Decision Engine listening on port ${port}`);
});
