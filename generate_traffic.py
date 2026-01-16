#!/usr/bin/env python3
"""
Real-time traffic generator - sends sample traffic through the threat detection pipeline.
Logs will be generated in the database service and visible on the dashboard.
"""
import json
import time
import random
from urllib.request import Request, urlopen
from urllib.error import URLError

CAPTURE_URL = "http://localhost:3001/capture"
LOGS_URL = "http://localhost:3006/logs"

def send_traffic(packets, bytes_sent, duration, label="test"):
    """Send a traffic sample to the capture service."""
    payload = {
        "packets": packets,
        "bytes": bytes_sent,
        "duration": duration,
        "ip": f"192.168.1.{random.randint(1, 254)}"
    }
    
    try:
        req = Request(
            CAPTURE_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        with urlopen(req, timeout=10) as r:
            response = json.loads(r.read().decode("utf-8"))
            print(f"[{label}] Status: {r.status} | Threat Level: {response.get('threat_level', 'N/A')}")
            return response
    except URLError as e:
        print(f"[{label}] Error: {e}")
        return None

def get_logs():
    """Fetch current threat logs from the database."""
    try:
        with urlopen(LOGS_URL, timeout=5) as r:
            logs = json.loads(r.read().decode("utf-8"))
            return logs
    except URLError as e:
        print(f"Error fetching logs: {e}")
        return []

def main():
    print("=" * 60)
    print("Shadow Guard - Real-Time Traffic Generator")
    print("=" * 60)
    print(f"Sending traffic to: {CAPTURE_URL}\n")
    
    # Send various traffic patterns
    traffic_patterns = [
        {"packets": 50, "bytes": 2000, "duration": 1.0, "label": "Benign (light)"},
        {"packets": 150, "bytes": 50000, "duration": 2.5, "label": "Benign (medium)"},
        {"packets": 500, "bytes": 500000, "duration": 5.0, "label": "Suspicious (high volume)"},
        {"packets": 1000, "bytes": 2000000, "duration": 2.0, "label": "High-risk (DDoS-like)"},
        {"packets": 75, "bytes": 35000, "duration": 1.5, "label": "Benign (normal)"},
    ]
    
    print(f"\nSending {len(traffic_patterns)} traffic samples...\n")
    
    for pattern in traffic_patterns:
        print(f"Sending: {pattern['label']}")
        send_traffic(
            pattern["packets"],
            pattern["bytes"],
            pattern["duration"],
            pattern["label"]
        )
        time.sleep(1)  # Brief pause between requests
    
    # Wait for processing
    print("\nWaiting for processing (5 seconds)...\n")
    time.sleep(5)
    
    # Fetch and display logs
    print("=" * 60)
    print("THREAT LOGS (from database)")
    print("=" * 60)
    logs = get_logs()
    
    if logs:
        if isinstance(logs, list):
            print(f"Total logs: {len(logs)}\n")
            for log in logs[-5:]:  # Show last 5 logs
                print(json.dumps(log, indent=2))
        else:
            print(json.dumps(logs, indent=2))
    else:
        print("No logs found yet. Check service connectivity.")
    
    print("\n" + "=" * 60)
    print("✓ Traffic generation complete!")
    print("View dashboard: http://localhost:7000")
    print("=" * 60)

if __name__ == "__main__":
    main()
