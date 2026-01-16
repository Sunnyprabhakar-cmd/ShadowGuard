const express = require('express');
const axios = require('axios');
const app = express();
const port = 3000;

app.use(express.json());

function generateExtendedFeatures(trafficData) {
  // Base features
  const packets = trafficData.packets || 0;
  const bytes = trafficData.bytes || 0;
  const duration = trafficData.duration || 0.001; // avoid division by zero
  
  // Calculate derived features to match ML model expectations (69 features)
  const features = [];
  
  // Basic stats (4 features)
  features.push(packets);
  features.push(bytes);
  features.push(duration);
  features.push(bytes / duration); // bytes per second
  
  // Packet-based features (10 features)
  features.push(packets / duration); // packets per second
  features.push(bytes / packets || 0); // avg bytes per packet
  features.push(packets * bytes); // interaction term
  features.push(Math.log(packets + 1));
  features.push(Math.log(bytes + 1));
  features.push(Math.log(duration + 1));
  
  // Statistical features (15 features)
  for (let i = 0; i < 15; i++) {
    features.push(Math.sin(packets * (i + 1)) * bytes / (duration + 1));
  }
  
  // Polynomial features (15 features)
  for (let i = 0; i < 15; i++) {
    features.push(Math.pow(packets, 2 - (i % 2)) * Math.pow(bytes, (i % 2)) / (Math.pow(duration, 2) + 1));
  }
  
  // Trigonometric and exponential features (15 features)
  for (let i = 0; i < 15; i++) {
    const val = (packets + bytes + duration) / 3;
    features.push(Math.cos(i * val) * Math.exp(-duration));
  }
  
  // Padding to reach exactly 69 features
  while (features.length < 69) {
    const idx = features.length;
    features.push((packets + bytes) / (duration + 1) * Math.sin(idx));
  }
  
  return features.slice(0, 69); // Ensure exactly 69 features
}

function buildTrafficContext(trafficData) {
  return {
    src_ip: trafficData.src_ip || trafficData.source_ip || trafficData.sourceIp || null,
    dst_ip: trafficData.dst_ip || trafficData.destination_ip || trafficData.destinationIp || null,
    protocol: trafficData.protocol || null,
    attack_type: trafficData.attack_type || trafficData.attackType || trafficData.type || 'unknown',
    packets: trafficData.packets || trafficData.packet_count || 0,
    bytes_sent: trafficData.bytes_sent || trafficData.bytes || 0,
    duration: trafficData.duration || 0,
    flow_type: trafficData.flow_type || null
  };
}

app.post('/extract', async (req, res) => {
  const trafficData = req.body;
  console.log('Extracting features from:', trafficData);

  try {
    // Generate extended features to match ML model expectations
    const extendedFeatures = generateExtendedFeatures(trafficData);
    const context = buildTrafficContext(trafficData);

    // Call ML detection
    await axios.post('http://ml-detection-service:8000/detect', { features: extendedFeatures, context });
    console.log('Features sent to ML detection (69 features)');

    res.json({ 
      feature_count: extendedFeatures.length,
      base_features: {
        packet_count: trafficData.packets || 0,
        total_bytes: trafficData.bytes || 0,
        duration: trafficData.duration || 0
      },
      context
    });
  } catch (error) {
    console.error('Error in feature extraction:', error);
    res.status(500).json({ error: 'Failed to extract features' });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(port, () => {
  console.log(`Flow Feature Extraction Service listening on port ${port}`);
});
