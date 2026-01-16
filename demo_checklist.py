#!/usr/bin/env python3
"""
Shadow Guard Demo - Pre-Demo Checklist
Run this script 30 minutes before your demo to verify all systems are ready
"""

import subprocess
import requests
import sys
import time
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_check(passed, message):
    """Print a check result"""
    status = f"{Colors.GREEN}✓ PASS{Colors.ENDC}" if passed else f"{Colors.RED}✗ FAIL{Colors.ENDC}"
    print(f"  {status} {message}")
    return passed

def check_docker():
    """Check if Docker is running"""
    try:
        subprocess.run(["docker", "ps"], capture_output=True, timeout=5, check=True)
        return True
    except:
        return False

def check_service(port, name, path="/health"):
    """Check if a service is responding"""
    try:
        url = f"http://localhost:{port}{path}"
        response = requests.get(url, timeout=3)
        return response.status_code in [200, 202]
    except:
        return False

def check_api_call(port, path, payload=None):
    """Test an API endpoint"""
    try:
        url = f"http://localhost:{port}{path}"
        if payload:
            response = requests.post(url, json=payload, timeout=3)
        else:
            response = requests.get(url, timeout=3)
        return response.status_code in [200, 202]
    except:
        return False

def check_database():
    """Check if database is responding"""
    try:
        result = subprocess.run(
            ["docker-compose", "exec", "-T", "threat-log-database-service",
             "psql", "-U", "postgres", "threat_db", "-c", "SELECT 1;"],
            capture_output=True, timeout=5, stdout=subprocess.DEVNULL
        )
        return result.returncode == 0
    except:
        return False

def check_models_exist():
    """Check if trained models exist"""
    try:
        import os
        iso_forest = os.path.exists("./models/isolation_forest.pkl")
        rand_forest = os.path.exists("./models/random_forest.pkl")
        return iso_forest and rand_forest
    except:
        return False

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}Shadow Guard - Pre-Demo Checklist{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}\n")
    
    all_passed = True
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # === INFRASTRUCTURE ===
    print(f"{Colors.BOLD}📋 Infrastructure Checks{Colors.ENDC}")
    
    docker_ok = check_docker()
    all_passed &= print_check(docker_ok, "Docker is running")
    
    if not docker_ok:
        print(f"\n{Colors.RED}❌ Docker is not running. Start Docker first.{Colors.ENDC}\n")
        return False
    
    # === SERVICES ===
    print(f"\n{Colors.BOLD}🔧 Service Health Checks{Colors.ENDC}")
    
    services = [
        (3001, "Traffic Capture", "Traffic Capture Service"),
        (3002, "Feature Extraction", "Feature Extraction Service"),
        (8001, "ML Detection", "ML Detection Service"),
        (8002, "Classification", "Classification Service"),
        (3003, "Decision Engine", "Playbook Decision Engine"),
        (3004, "Alert Service", "Alert Notification Service"),
        (3005, "Response Service", "Automated Response Service"),
        (3006, "Database API", "Threat Log Database Service"),
        (8003, "Model Training", "Model Training Service"),
        (7000, "Dashboard", "Threat Dashboard Service"),
    ]
    
    services_ok = True
    for port, name, full_name in services:
        check = check_service(port, name)
        services_ok &= check
        all_passed &= print_check(check, f"{name:25} (port {port})")
        if not check:
            print(f"     {Colors.YELLOW}→ Run: docker-compose logs {name.lower().replace(' ', '-')}{Colors.ENDC}")
    
    # === DATABASE ===
    print(f"\n{Colors.BOLD}💾 Database Checks{Colors.ENDC}")
    
    db_ok = check_database()
    all_passed &= print_check(db_ok, "Database is accessible")
    
    # === ML MODELS ===
    print(f"\n{Colors.BOLD}🤖 ML Model Checks{Colors.ENDC}")
    
    models_ok = check_models_exist()
    all_passed &= print_check(models_ok, "Isolation Forest model exists")
    all_passed &= print_check(models_ok, "Random Forest model exists")
    
    if not models_ok:
        print(f"     {Colors.YELLOW}→ Models not found. Run training first:{Colors.ENDC}")
        print(f"     {Colors.YELLOW}  docker-compose up model-training-service{Colors.ENDC}")
    
    # === API ENDPOINTS ===
    print(f"\n{Colors.BOLD}📡 API Endpoint Tests{Colors.ENDC}")
    
    test_payload = {
        "packets": 100,
        "bytes": 5000,
        "duration": 1,
        "src_ip": "192.168.1.1",
        "dst_ip": "192.168.1.100",
        "protocol": "TCP"
    }
    
    capture_ok = check_api_call(3001, "/capture", test_payload)
    all_passed &= print_check(capture_ok, "POST /capture (Traffic Capture)")
    
    stats_ok = check_api_call(7000, "/api/statistics")
    all_passed &= print_check(stats_ok, "GET /api/statistics (Dashboard)")
    
    logs_ok = check_api_call(3006, "/logs")
    all_passed &= print_check(logs_ok, "GET /logs (Database API)")
    
    # === DEMO GENERATOR ===
    print(f"\n{Colors.BOLD}🎬 Demo Generator Checks{Colors.ENDC}")
    
    try:
        import os
        demo_ok = os.path.exists("./demo_log_generator.py")
        all_passed &= print_check(demo_ok, "demo_log_generator.py exists")
    except:
        all_passed &= print_check(False, "demo_log_generator.py exists")
    
    try:
        import importlib.util
        requests_ok = importlib.util.find_spec("requests") is not None
        all_passed &= print_check(requests_ok, "Python requests library installed")
    except:
        all_passed &= print_check(False, "Python requests library installed")
    
    # === SUMMARY ===
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
    
    if all_passed:
        print(f"{Colors.BOLD}{Colors.GREEN}✓ ALL CHECKS PASSED{Colors.ENDC}")
        print(f"\n{Colors.GREEN}Your demo environment is ready!{Colors.ENDC}")
        print(f"\n{Colors.BOLD}Next steps:{Colors.ENDC}")
        print(f"  1. Open browser: {Colors.BLUE}http://localhost:7000{Colors.ENDC}")
        print(f"  2. Run demo:     {Colors.BLUE}python3 demo_log_generator.py{Colors.ENDC}")
        print(f"  3. Select:       {Colors.BLUE}Choose scenario (1-9){Colors.ENDC}")
        print(f"\n{Colors.BOLD}Recommendation:{Colors.ENDC}")
        print(f"  Start with Scenario 4 (Normal Traffic) to show baseline,")
        print(f"  then Scenario 2 (DDoS) for impact, then Scenario 7 for complexity.\n")
        return True
    else:
        print(f"{Colors.BOLD}{Colors.RED}✗ SOME CHECKS FAILED{Colors.ENDC}")
        print(f"\n{Colors.RED}Please fix the above issues before proceeding.{Colors.ENDC}")
        print(f"\n{Colors.YELLOW}Quick fixes:{Colors.ENDC}")
        print(f"  • Start services:    {Colors.BLUE}docker-compose up -d{Colors.ENDC}")
        print(f"  • View logs:         {Colors.BLUE}docker-compose logs <service>{Colors.ENDC}")
        print(f"  • Train models:      {Colors.BLUE}docker-compose up model-training-service{Colors.ENDC}")
        print(f"  • Wait & retry:      {Colors.BLUE}sleep 30 && python3 demo_checklist.py{Colors.ENDC}\n")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
