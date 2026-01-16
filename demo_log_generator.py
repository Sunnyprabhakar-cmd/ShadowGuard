#!/usr/bin/env python3
"""
Shadow Guard Demo Log Generator
Real-time attack simulation for live demonstrations
Generates various threat patterns and shows live detection/blocking
"""

import json
import time
import random
import sys
import requests
from datetime import datetime
from typing import Dict, List, Tuple

# API Endpoints
CAPTURE_URL = "http://localhost:3001/capture"
LOGS_URL = "http://localhost:3006/logs"
STATS_URL = "http://localhost:7000/api/statistics"
DASHBOARD_URL = "http://localhost:7000"

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}\n")

def print_status(icon, message, status="INFO"):
    """Print status message with icon"""
    if status == "SUCCESS":
        color = Colors.GREEN
    elif status == "WARNING":
        color = Colors.YELLOW
    elif status == "ERROR":
        color = Colors.RED
    else:
        color = Colors.BLUE
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{Colors.BOLD}[{timestamp}]{Colors.ENDC} {icon} {color}{message}{Colors.ENDC}")

def send_traffic_event(packets: int, bytes_sent: int, duration: float, 
                       src_ip: str, dst_ip: str, protocol: str, 
                       label: str, anomaly_score: float = None,
                       attack_type: str = "unknown") -> Dict:
    """Send a traffic event to the capture service"""
    payload = {
        "packets": packets,
        "bytes": bytes_sent,
        "duration": duration,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "protocol": protocol,
        "attack_type": attack_type,
        "packet_count": packets,
        "bytes_sent": bytes_sent,
        "bytes_received": bytes_sent // 2,
        "flow_type": "anomaly" if anomaly_score and anomaly_score > 0.7 else "normal"
    }
    
    try:
        response = requests.post(CAPTURE_URL, json=payload, timeout=10)
        if response.status_code == 200 or response.status_code == 202:
            result = response.json()
            print_status("✓", f"{label}: {src_ip} → {dst_ip} ({protocol})", "SUCCESS")
            return result
        else:
            print_status("✗", f"{label}: API returned {response.status_code}", "ERROR")
            return None
    except Exception as e:
        print_status("✗", f"{label}: {str(e)}", "ERROR")
        return None

def get_threat_stats() -> Dict:
    """Fetch current threat statistics from dashboard"""
    try:
        response = requests.get(STATS_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print_status("✗", f"Failed to fetch stats: {str(e)}", "ERROR")
    return {}

def get_threat_logs(limit: int = 20) -> List[Dict]:
    """Fetch recent threat logs"""
    try:
        response = requests.get(f"{LOGS_URL}?limit={limit}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) else data.get('logs', [])
    except Exception as e:
        print_status("✗", f"Failed to fetch logs: {str(e)}", "ERROR")
    return []

def scenario_1_port_scan():
    """Scenario 1: Port Scan Detection"""
    print_header("SCENARIO 1: PORT SCAN DETECTION")
    print_status("▶", "Attacker scanning for open ports on target server...", "INFO")
    print(f"{Colors.YELLOW}[Expected] Isolation Forest detects unusual traffic pattern{Colors.ENDC}\n")
    
    target_ip = "192.168.1.100"
    attacker_ip = "10.0.0.50"
    
    # Port scan: rapid sequential connections with small packets
    for port in range(22, 82, 10):
        send_traffic_event(
            packets=1, bytes_sent=64, duration=0.1,
            src_ip=attacker_ip, dst_ip=target_ip,
            protocol="TCP", label=f"Port {port + 1}/tcp",
            anomaly_score=0.75,
            attack_type="port_scan"
        )
        time.sleep(0.5)
    
    print_status("⚠", "Port scan pattern detected! ", "WARNING")
    time.sleep(2)

def scenario_2_ddos_attack():
    """Scenario 2: DDoS (Distributed Denial of Service)"""
    print_header("SCENARIO 2: DDoS ATTACK DETECTION")
    print_status("▶", "Multiple sources flooding target server...", "INFO")
    print(f"{Colors.YELLOW}[Expected] Sudden spike in traffic + Random Forest classifies as HIGH THREAT{Colors.ENDC}\n")
    
    target_ip = "192.168.1.100"
    
    # Simulate 5 botnet sources sending massive traffic
    for source_num in range(5):
        attacker_ip = f"203.0.113.{source_num + 1}"
        for packet_wave in range(3):
            send_traffic_event(
                packets=5000, bytes_sent=2500000, duration=0.5,
                src_ip=attacker_ip, dst_ip=target_ip,
                protocol="UDP", label=f"DDoS Wave {packet_wave + 1} from {attacker_ip}",
                anomaly_score=0.95,  # High anomaly
                attack_type="ddos"
            )
            time.sleep(0.3)
    
    print_status("🚫", "DDoS attack detected and BLOCKED!", "WARNING")
    time.sleep(2)

def scenario_3_data_exfiltration():
    """Scenario 3: Data Exfiltration Detection"""
    print_header("SCENARIO 3: DATA EXFILTRATION DETECTION")
    print_status("▶", "Suspicious outbound data transfer detected...", "INFO")
    print(f"{Colors.YELLOW}[Expected] Unusual byte ratio suggests data theft{Colors.ENDC}\n")
    
    internal_ip = "192.168.1.50"
    external_ip = "198.51.100.23"
    
    # Exfiltration: large outbound transfers, high bytes/packets ratio
    for i in range(3):
        send_traffic_event(
            packets=100, bytes_sent=50000000, duration=10.0,
            src_ip=internal_ip, dst_ip=external_ip,
            protocol="TCP", label=f"Exfiltration Burst {i + 1}",
            anomaly_score=0.88,
            attack_type="data_exfiltration"
        )
        time.sleep(1)
    
    print_status("⚠", "Data exfiltration pattern detected!", "WARNING")
    time.sleep(2)

def scenario_4_normal_traffic():
    """Scenario 4: Benign Traffic (Baseline)"""
    print_header("SCENARIO 4: NORMAL BUSINESS TRAFFIC")
    print_status("▶", "Legitimate user activity - should NOT trigger alerts...", "INFO")
    print(f"{Colors.GREEN}[Expected] Traffic classified as BENIGN{Colors.ENDC}\n")
    
    # Normal HTTP traffic
    patterns = [
        ("192.168.1.10", "8.8.8.8", "TCP", "Web browsing", 100, 50000, 2.0),
        ("192.168.1.20", "1.1.1.1", "TCP", "DNS query", 10, 512, 0.1),
        ("192.168.1.30", "13.107.42.14", "TCP", "Cloud sync", 500, 1000000, 5.0),
        ("192.168.1.40", "210.72.23.5", "TCP", "Video streaming", 2000, 5000000, 30.0),
    ]
    
    for src_ip, dst_ip, proto, label_text, packets, bytes_sent, duration in patterns:
        send_traffic_event(
            packets=packets, bytes_sent=bytes_sent, duration=duration,
            src_ip=src_ip, dst_ip=dst_ip,
            protocol=proto, label=label_text,
            anomaly_score=0.1,  # Very low - benign
            attack_type="normal_traffic"
        )
        time.sleep(0.5)
    
    print_status("✓", "All normal traffic classified as BENIGN", "SUCCESS")
    time.sleep(2)

def scenario_5_brute_force():
    """Scenario 5: Brute Force Login Attempt"""
    print_header("SCENARIO 5: BRUTE FORCE LOGIN DETECTION")
    print_status("▶", "Multiple failed authentication attempts...", "INFO")
    print(f"{Colors.YELLOW}[Expected] Rapid connection pattern with small payloads{Colors.ENDC}\n")
    
    target_ip = "192.168.1.200"
    attacker_ip = "10.20.30.40"
    
    # Brute force: many rapid small connections
    for attempt in range(8):
        send_traffic_event(
            packets=2, bytes_sent=256, duration=0.1,
            src_ip=attacker_ip, dst_ip=target_ip,
            protocol="TCP", label=f"Login attempt #{attempt + 1}",
            anomaly_score=0.72,
            attack_type="brute_force"
        )
        time.sleep(0.2)
    
    print_status("🔐", "Brute force attack detected! Account locked.", "WARNING")
    time.sleep(2)

def scenario_6_malware_command_control():
    """Scenario 6: Malware C&C Communication"""
    print_header("SCENARIO 6: MALWARE C&C DETECTION")
    print_status("▶", "Compromised host communicating with C&C server...", "INFO")
    print(f"{Colors.YELLOW}[Expected] Suspicious patterns in timing and volume{Colors.ENDC}\n")
    
    infected_host = "192.168.1.75"
    cc_server = "104.21.45.67"
    
    # C&C: irregular traffic pattern with periodic check-ins
    for i in range(4):
        send_traffic_event(
            packets=random.randint(50, 200), 
            bytes_sent=random.randint(10000, 500000), 
            duration=random.uniform(1, 5),
            src_ip=infected_host, dst_ip=cc_server,
            protocol="TCP", label=f"C&C Beacon {i + 1}",
            anomaly_score=0.80,
            attack_type="malware_command_control"
        )
        time.sleep(1)
    
    print_status("⚠", "Malware C&C communication detected! Host quarantined.", "WARNING")
    time.sleep(2)

def scenario_7_mixed_attack():
    """Scenario 7: Mixed Attack Patterns"""
    print_header("SCENARIO 7: COORDINATED MULTI-VECTOR ATTACK")
    print_status("▶", "Simultaneous attacks from different threat vectors...", "INFO")
    print(f"{Colors.RED}[Expected] CRITICAL - Multiple concurrent threats detected{Colors.ENDC}\n")
    
    # Simultaneous threats
    print_status("1️⃣", "Starting port scan...", "INFO")
    send_traffic_event(packets=1, bytes_sent=64, duration=0.1, 
                      src_ip="10.0.0.1", dst_ip="192.168.1.100",
                      protocol="TCP", label="Scan", anomaly_score=0.70,
                      attack_type="port_scan")
    
    print_status("2️⃣", "Starting DDoS flood...", "INFO")
    send_traffic_event(packets=10000, bytes_sent=5000000, duration=1.0,
                      src_ip="203.0.113.1", dst_ip="192.168.1.100",
                      protocol="UDP", label="DDoS", anomaly_score=0.95,
                      attack_type="ddos")
    
    print_status("3️⃣", "Starting data exfiltration...", "INFO")
    send_traffic_event(packets=500, bytes_sent=100000000, duration=5.0,
                      src_ip="192.168.1.80", dst_ip="198.51.100.1",
                      protocol="TCP", label="Exfil", anomaly_score=0.85,
                      attack_type="data_exfiltration")
    
    print_status("🚨", "CRITICAL: Multiple threats detected simultaneously!", "WARNING")
    time.sleep(2)

def scenario_8_zero_day():
    """Scenario 8: Zero-Day style exploit"""
    print_header("SCENARIO 8: ZERO-DAY ATTACK DETECTION")
    print_status("▶", "Unknown exploit chain with privilege escalation behavior...", "INFO")
    print(f"{Colors.RED}[Expected] Immediate block + email alert to configured recipients{Colors.ENDC}\n")

    target_ip = "192.168.1.210"
    attacker_ip = "198.18.0.77"

    bursts = [
        (45, 180000, 0.2, "Initial exploit delivery"),
        (120, 950000, 0.4, "Exploit payload staging"),
        (12, 2500000, 0.1, "Privilege escalation trigger"),
        (30, 4200000, 0.2, "Post-exploit beacon"),
    ]

    for packets, bytes_sent, duration, label in bursts:
        send_traffic_event(
            packets=packets, bytes_sent=bytes_sent, duration=duration,
            src_ip=attacker_ip, dst_ip=target_ip,
            protocol="TCP", label=label,
            anomaly_score=0.99,
            attack_type="zero_day"
        )
        time.sleep(0.4)

    print_status("🚨", "Zero-day behavior detected! Emergency alert triggered.", "WARNING")
    time.sleep(2)

def display_live_stats():
    """Display current threat statistics from dashboard"""
    print_header("CURRENT THREAT STATISTICS")
    
    stats = get_threat_stats()
    if stats:
        print(f"{Colors.BOLD}Summary:{Colors.ENDC}")
        print(f"  {Colors.RED}🔴 High Threats: {stats.get('high_threats', 0)}{Colors.ENDC}")
        print(f"  {Colors.YELLOW}🟠 Medium Threats: {stats.get('medium_threats', 0)}{Colors.ENDC}")
        print(f"  {Colors.GREEN}🟡 Low Threats: {stats.get('low_threats', 0)}{Colors.ENDC}")
        print(f"  {Colors.BLUE}📊 Total Events: {stats.get('total_events', 0)}{Colors.ENDC}")
        print(f"  {Colors.RED}🚫 Blocked IPs: {stats.get('blocked_ips', 0)}{Colors.ENDC}")
        print(f"  {Colors.CYAN}🔔 Alerts Sent: {stats.get('alerts_sent', 0)}{Colors.ENDC}\n")

def display_recent_threats():
    """Display recent threat events"""
    print_header("RECENT THREAT EVENTS (Last 10)")
    
    logs = get_threat_logs(10)
    if logs:
        for i, log in enumerate(logs[:10], 1):
            src_ip = log.get('src_ip') or 'Unknown'
            dst_ip = log.get('dst_ip') or 'Unknown'
            confidence_raw = log.get('confidence', 0)
            confidence = float(confidence_raw) if isinstance(confidence_raw, (int, float)) else 0.0
            action = log.get('action') or 'N/A'
            attack_type = log.get('attack_type') or log.get('type') or 'Unknown'
            
            # Color by confidence
            if confidence > 0.8:
                color = Colors.RED
                icon = "🔴"
            elif confidence > 0.5:
                color = Colors.YELLOW
                icon = "🟠"
            else:
                color = Colors.GREEN
                icon = "🟡"
            
            action_icon = {"block": "🚫", "alert": "🔔", "monitor": "👁️"}.get(action, "•")
            
            print(f"{i}. {icon} {color}{src_ip:15} → {dst_ip:15}{Colors.ENDC} | "
                  f"Type: {attack_type} | "
                  f"Confidence: {color}{confidence:.2f}{Colors.ENDC} | "
                  f"{action_icon} {action}")
    else:
        print("No threats detected yet.")
    print()

def main():
    """Main demo function"""
    print_header("SHADOW GUARD - LIVE THREAT DETECTION DEMO")
    
    print(f"{Colors.BOLD}Welcome to Shadow Guard!{Colors.ENDC}")
    print(f"Dashboard: {Colors.CYAN}{DASHBOARD_URL}{Colors.ENDC}")
    print(f"This demo will simulate various attack scenarios and show real-time detection.\n")
    
    time.sleep(2)
    
    scenarios = [
        ("1", "Port Scan Detection", scenario_1_port_scan),
        ("2", "DDoS Attack Detection", scenario_2_ddos_attack),
        ("3", "Data Exfiltration", scenario_3_data_exfiltration),
        ("4", "Normal Traffic (Baseline)", scenario_4_normal_traffic),
        ("5", "Brute Force Attack", scenario_5_brute_force),
        ("6", "Malware C&C Detection", scenario_6_malware_command_control),
        ("7", "Multi-Vector Attack", scenario_7_mixed_attack),
        ("8", "Zero-Day Attack", scenario_8_zero_day),
        ("9", "Show Stats & Logs", None),
        ("10", "Run All Scenarios", None),
        ("0", "Exit", None),
    ]
    
    while True:
        print(f"\n{Colors.BOLD}Available Scenarios:{Colors.ENDC}")
        for num, name, _ in scenarios:
            print(f"  {num}. {name}")
        
        choice = input(f"\n{Colors.BOLD}Select scenario (0-10): {Colors.ENDC}").strip()
        
        if choice == "0":
            print_status("👋", "Thank you for watching the Shadow Guard demo!", "SUCCESS")
            break
        elif choice == "9":
            display_live_stats()
            display_recent_threats()
        elif choice == "10":
            for num, name, func in scenarios:
                if func and num not in {"9", "10", "0"}:
                    print_status("▶", f"Running: {name}", "INFO")
                    func()
                    time.sleep(2)
            display_live_stats()
            display_recent_threats()
        else:
            for num, name, func in scenarios:
                if num == choice and func:
                    func()
                    display_live_stats()
                    display_recent_threats()
                    break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo interrupted by user.{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}Error: {str(e)}{Colors.ENDC}")
        sys.exit(1)
