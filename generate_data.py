#!/usr/bin/env python3
import pandas as pd
import numpy as np
import os

os.makedirs('./data', exist_ok=True)

# Generate sample data
np.random.seed(42)
n_samples = 1000
data = {
    'packet_size': np.random.randint(50, 1500, n_samples),
    'duration': np.random.exponential(2.0, n_samples),
    'protocol': np.random.choice(['tcp', 'udp', 'icmp'], n_samples),
    'packet_count': np.random.randint(1, 100, n_samples),
    'bytes_sent': np.random.randint(1000, 1000000, n_samples),
    'bytes_received': np.random.randint(1000, 1000000, n_samples),
    'flow_type': np.random.choice(['normal', 'anomaly'], n_samples, p=[0.95, 0.05])
}

df = pd.DataFrame(data)
df.to_parquet('./data/sample_traffic.parquet')
num_anomalies = (df.flow_type == 'anomaly').sum()
print(f"✓ Data created: ./data/sample_traffic.parquet")
print(f"  Samples: {len(df)}, Features: {len(df.columns)}")
print(f"  Normal: {len(df) - num_anomalies}, Anomalies: {num_anomalies}")
