const express = require('express');
const axios = require('axios');
const app = express();
const port = 3000;

app.use(express.json());

app.post('/capture', async (req, res) => {
  const trafficData = req.body;
  console.log('Captured traffic data:', trafficData);

  try {
    // Call feature extraction
    await axios.post('http://flow-feature-extraction-service:3000/extract', trafficData);
    console.log('Traffic data sent to feature extraction');

    res.json({ message: 'Traffic data captured and processed', data: trafficData });
  } catch (error) {
    console.error('Error in traffic capture:', error);
    res.status(500).json({ error: 'Failed to capture traffic' });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(port, () => {
  console.log(`Traffic Capture Service listening on port ${port}`);
});