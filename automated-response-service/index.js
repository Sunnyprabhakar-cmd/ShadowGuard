const express = require('express');
const axios = require('axios');
const { spawn } = require('child_process');
const net = require('net');
const app = express();
const port = 3000;
const enableLocalIptables = process.env.ENABLE_LOCAL_IPTABLES === 'true';

app.use(express.json());

function isValidIp(ip) {
  return net.isIP(ip) !== 0;
}

function runIptablesBlock(ip) {
  return new Promise((resolve, reject) => {
    const blockInput = spawn('iptables', ['-C', 'INPUT', '-s', ip, '-j', 'DROP']);
    blockInput.on('exit', (code) => {
      if (code === 0) {
        resolve('IP already blocked in INPUT chain');
        return;
      }

      const addInput = spawn('iptables', ['-A', 'INPUT', '-s', ip, '-j', 'DROP']);
      addInput.on('exit', (addCode) => {
        if (addCode !== 0) {
          reject(new Error('Failed to add INPUT block rule'));
          return;
        }

        const addOutput = spawn('iptables', ['-A', 'OUTPUT', '-d', ip, '-j', 'DROP']);
        addOutput.on('exit', (outCode) => {
          if (outCode !== 0) {
            reject(new Error('Failed to add OUTPUT block rule'));
            return;
          }
          resolve('IP blocked in INPUT and OUTPUT chains');
        });
      });
    });
  });
}

app.post('/respond', async (req, res) => {
  const { action, details } = req.body;
  const responseDetails = details || {};
  console.log('Executing response for action:', action);

  try {
    if (action === 'block' && responseDetails.ip) {
      const ip = responseDetails.ip;
      if (!isValidIp(ip)) {
        return res.status(400).json({ error: 'Invalid IP for block action' });
      }

      console.log(`Blocking IP: ${ip}`);

      if (enableLocalIptables) {
        await runIptablesBlock(ip);
      } else {
        console.log('ENABLE_LOCAL_IPTABLES is false; block action recorded but not applied locally');
      }
    } else if (action === 'alert') {
      console.log('Alert action: monitoring increased');
    } else if (action === 'manual-review') {
      console.log('Manual review required for this event');
    }

    // Log the response
    await axios.post('http://threat-log-database-service:3000/log', {
      type: responseDetails.attack_type || responseDetails.attackType || 'response',
      action,
      details: responseDetails,
      timestamp: new Date().toISOString()
    });
    console.log('Response logged');

    res.json({ message: 'Response executed and logged' });
  } catch (error) {
    console.error('Error in response service:', error);
    res.status(500).json({ error: 'Failed to execute response' });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(port, () => {
  console.log(`Automated Response Service listening on port ${port}`);
});
