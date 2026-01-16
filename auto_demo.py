#!/usr/bin/env python3
"""
Shadow Guard - Auto Demo Log Generator
Continuously cycles through all attack scenarios for live demos.
Run automatically by start_demo.sh, or manually: python3 auto_demo.py
"""

import json
import time
import random
import sys
import os
from urllib.request import Request, urlopen
from urllib.error import URLError

CAPTURE_URL = os.getenv("CAPTURE_URL", "http://localhost:3001/capture")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:7000")
RESET_LOGS_URL = os.getenv("RESET_LOGS_URL", "")

class C:
    HEADER = '\033[95m'
    BLUE   = '\033[94m'
    CYAN   = '\033[96m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    END    = '\033[0m'
    BOLD   = '\033[1m'

def log(icon, msg, color=C.BLUE):
    from datetime import datetime
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{C.BOLD}[{ts}]{C.END} {icon} {color}{msg}{C.END}", flush=True)

def send(packets, bytes_sent, duration, src_ip, dst_ip, protocol, attack_type, label):
    payload = {
        "packets": packets, "bytes": bytes_sent, "duration": duration,
        "src_ip": src_ip, "dst_ip": dst_ip, "protocol": protocol,
        "attack_type": attack_type, "packet_count": packets,
        "bytes_sent": bytes_sent, "bytes_received": bytes_sent // 2,
        "flow_type": "anomaly" if attack_type != "normal_traffic" else "normal"
    }
    try:
        req = Request(CAPTURE_URL, data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=10) as r:
            result = json.loads(r.read().decode())
            action = result.get("action", result.get("threat_level", "N/A"))
            conf   = result.get("confidence", "")
            conf_str = f" | conf: {float(conf):.2f}" if conf != "" else ""
            log("✓", f"{label}: {src_ip} → {dst_ip}{conf_str} | {action}", C.GREEN)
    except URLError as e:
        log("✗", f"{label}: {e}", C.RED)

# ── Scenarios ────────────────────────────────────────────────────────────────

def port_scan():
    log("▶", "PORT SCAN — attacker probing open ports", C.CYAN)
    attacker, target = "10.0.0.50", "192.168.1.100"
    for port in range(22, 82, 10):
        send(1, 64, 0.1, attacker, target, "TCP", "port_scan", f"Port {port}/tcp")
        time.sleep(0.4)

def ddos():
    log("▶", "DDoS ATTACK — botnet flooding target", C.RED)
    target = "192.168.1.100"
    for i in range(5):
        src = f"203.0.113.{i+1}"
        for w in range(2):
            send(5000, 2500000, 0.5, src, target, "UDP", "ddos", f"Wave {w+1} from {src}")
            time.sleep(0.2)

def exfiltration():
    log("▶", "DATA EXFILTRATION — large outbound transfer", C.YELLOW)
    for i in range(3):
        send(100, 50000000, 10.0, "192.168.1.50", "198.51.100.23",
             "TCP", "data_exfiltration", f"Exfil burst {i+1}")
        time.sleep(0.8)

def normal_traffic():
    log("▶", "NORMAL TRAFFIC — baseline benign activity", C.GREEN)
    flows = [
        (100,   50000,   2.0,  "192.168.1.10", "8.8.8.8",        "TCP", "Web browse"),
        (10,    512,     0.1,  "192.168.1.20", "1.1.1.1",         "UDP", "DNS query"),
        (500,   1000000, 5.0,  "192.168.1.30", "13.107.42.14",    "TCP", "Cloud sync"),
        (2000,  5000000, 30.0, "192.168.1.40", "210.72.23.5",     "TCP", "Streaming"),
    ]
    for pkts, byt, dur, src, dst, proto, lbl in flows:
        send(pkts, byt, dur, src, dst, proto, "normal_traffic", lbl)
        time.sleep(0.4)

def brute_force():
    log("▶", "BRUTE FORCE — rapid login attempts", C.YELLOW)
    for i in range(8):
        send(2, 256, 0.1, "10.20.30.40", "192.168.1.200",
             "TCP", "brute_force", f"Login attempt #{i+1}")
        time.sleep(0.15)

def malware_cc():
    log("▶", "MALWARE C&C — infected host beaconing", C.RED)
    for i in range(4):
        send(random.randint(50, 200), random.randint(10000, 500000),
             random.uniform(1, 5), "192.168.1.75", "104.21.45.67",
             "TCP", "malware_command_control", f"Beacon {i+1}")
        time.sleep(0.9)

def multi_vector():
    log("▶", "MULTI-VECTOR — coordinated simultaneous attack", C.RED)
    send(1,     64,        0.1, "10.0.0.1",     "192.168.1.100", "TCP", "port_scan",         "Scan")
    send(10000, 5000000,   1.0, "203.0.113.1",  "192.168.1.100", "UDP", "ddos",              "DDoS flood")
    send(500,   100000000, 5.0, "192.168.1.80", "198.51.100.1",  "TCP", "data_exfiltration", "Exfil")
    time.sleep(0.5)

def zero_day():
    log("▶", "ZERO-DAY — unknown exploit chain", C.RED)
    phases = [
        (45, 180000, 0.2, "198.18.0.77", "192.168.1.210", "TCP", "Initial exploit"),
        (120, 950000, 0.4, "198.18.0.77", "192.168.1.210", "TCP", "Payload stage"),
        (12, 2500000, 0.1, "198.18.0.77", "192.168.1.210", "TCP", "Privilege escalation"),
        (30, 4200000, 0.2, "198.18.0.77", "192.168.1.210", "TCP", "Beacon"),
    ]
    for pkts, byt, dur, src, dst, proto, lbl in phases:
        send(pkts, byt, dur, src, dst, proto, "zero_day", lbl)
        time.sleep(0.3)

SCENARIOS = [
    ("Port Scan",       port_scan),
    ("DDoS Attack",     ddos),
    ("Data Exfil",      exfiltration),
    ("Normal Traffic",  normal_traffic),
    ("Brute Force",     brute_force),
    ("Malware C&C",     malware_cc),
    ("Multi-Vector",    multi_vector),
    ("Zero-Day",        zero_day),
]

# ── Wait for capture service ──────────────────────────────────────────────────

def wait_for_service(retries=30, delay=5):
    print(f"{C.BOLD}{C.CYAN}Waiting for Shadow Guard services...{C.END}", flush=True)
    for i in range(retries):
        try:
            req = Request(CAPTURE_URL.replace("/capture", "/health"))
            with urlopen(req, timeout=3):
                log("✓", "Services ready — starting demo loop", C.GREEN)
                return True
        except Exception:
            print(f"  [{i+1}/{retries}] Not ready yet, retrying in {delay}s...", flush=True)
            time.sleep(delay)
    log("✗", "Services did not become ready. Exiting.", C.RED)
    return False

def reset_logs():
    if not RESET_LOGS_URL:
        return

    try:
        req = Request(RESET_LOGS_URL, data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=10) as r:
            body = r.read().decode("utf-8", "replace")
            log("✓", f"Threat logs reset for clean demo state: {body}", C.GREEN)
    except Exception as exc:
        log("⚠", f"Could not reset threat logs automatically: {exc}", C.YELLOW)

# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    print(f"\n{C.BOLD}{C.CYAN}{'='*60}{C.END}")
    print(f"{C.BOLD}{C.CYAN}  Shadow Guard — Auto Demo Log Generator{C.END}")
    print(f"{C.BOLD}{C.CYAN}  Dashboard → {DASHBOARD_URL}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'='*60}{C.END}\n", flush=True)

    if not wait_for_service():
        sys.exit(1)

    reset_logs()

    cycle = 0
    while True:
        cycle += 1
        print(f"\n{C.BOLD}{C.YELLOW}── Cycle {cycle} ──────────────────────────────────────{C.END}", flush=True)
        for name, fn in SCENARIOS:
            print(f"\n{C.BOLD}[ {name} ]{C.END}", flush=True)
            fn()
            time.sleep(2)   # pause between scenarios so dashboard updates are visible
        log("↺", f"Cycle {cycle} complete — restarting in 5s (Ctrl+C to stop)", C.CYAN)
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}Demo stopped.{C.END}")
        sys.exit(0)
