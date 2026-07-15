#!/usr/bin/env python3
"""
Feature 26 (Jobs Portal) Backend Smoke Test - Sprint 2
Quick verification of critical endpoints
"""

import requests
import json
import sys
from typing import Dict, Any, Tuple

# Backend URL from frontend/.env
BACKEND_URL = "https://visa-polish-v2.preview.emergentagent.com"

# Test credentials
ADMIN_CREDS = {
    "email": "admin@realaicoach.app",
    "password": "NewAdminPass2026!"
}

EMPLOYER_CREDS = {
    "email": "e2e.employer.feature26@realaicoach.app",
    "password": "E2EEmployer#Feature26!2026"
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_test(name: str, status: str, details: str = ""):
    status_color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
    print(f"{status_color}[{status}]{Colors.RESET} {name}")
    if details:
        print(f"       {details}")

def login(credentials: Dict[str, str], user_type: str) -> Tuple[requests.Session, bool, str]:
    """Login and return session"""
    session = requests.Session()
    
    try:
        response = session.post(
            f"{BACKEND_URL}/api/auth/login",
            json=credentials,
            headers={
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            user_id = data.get("user_id", "unknown")
            return session, True, f"Login successful (user_id: {user_id})"
        else:
            return session, False, f"Login failed: {response.status_code} - {response.text[:200]}"
    except Exception as e:
        return session, False, f"Login error: {str(e)}"

def test_health_endpoint(session: requests.Session) -> Tuple[bool, str]:
    """Test GET /api/hiring/v2/health"""
    try:
        response = session.get(
            f"{BACKEND_URL}/api/hiring/v2/health",
            timeout=30
        )
        
        if response.status_code != 200:
            return False, f"Status {response.status_code} (expected 200)"
        
        data = response.json()
        feature_number = data.get("feature_number")
        feature_id = data.get("feature_id")
        
        if feature_number != 26:
            return False, f"feature_number={feature_number} (expected 26)"
        
        if feature_id != "jobs-portal":
            return False, f"feature_id={feature_id} (expected 'jobs-portal')"
        
        return True, f"Status 200, feature_number=26, feature_id=jobs-portal"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_pipeline_board(session: requests.Session) -> Tuple[bool, str]:
    """Test GET /api/jobs/employer/pipeline-board"""
    try:
        response = session.get(
            f"{BACKEND_URL}/api/jobs/employer/pipeline-board",
            timeout=30
        )
        
        if response.status_code == 500:
            return False, f"Status 500 (server error) - {response.text[:200]}"
        
        return True, f"Status {response.status_code} (not 500)"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_sla_alerts(session: requests.Session) -> Tuple[bool, str]:
    """Test GET /api/jobs/employer/sla-alerts"""
    try:
        response = session.get(
            f"{BACKEND_URL}/api/jobs/employer/sla-alerts",
            timeout=30
        )
        
        if response.status_code == 500:
            return False, f"Status 500 (server error) - {response.text[:200]}"
        
        return True, f"Status {response.status_code} (not 500)"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_offers(session: requests.Session) -> Tuple[bool, str]:
    """Test GET /api/jobs/employer/offers"""
    try:
        response = session.get(
            f"{BACKEND_URL}/api/jobs/employer/offers",
            timeout=30
        )
        
        if response.status_code == 500:
            return False, f"Status 500 (server error) - {response.text[:200]}"
        
        return True, f"Status {response.status_code} (not 500)"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_purge_endpoint(session: requests.Session) -> Tuple[bool, str]:
    """Test POST /api/jobs/save/test_final_purge"""
    try:
        response = session.post(
            f"{BACKEND_URL}/api/jobs/save/test_final_purge",
            json={},
            headers={
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest"
            },
            timeout=30
        )
        
        # Expected: 410 (Gone) or 401 (Unauthorized)
        if response.status_code in [410, 401]:
            return True, f"Status {response.status_code} (expected 410 or 401)"
        
        return False, f"Status {response.status_code} (expected 410 or 401)"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    print_header("Feature 26 (Jobs Portal) Backend Smoke Test - Sprint 2")
    
    results = {
        "admin": {"passed": 0, "failed": 0, "tests": []},
        "employer": {"passed": 0, "failed": 0, "tests": []}
    }
    
    # Test with Admin
    print_header("Testing with Admin User")
    admin_session, admin_login_ok, admin_login_msg = login(ADMIN_CREDS, "admin")
    
    if admin_login_ok:
        print_test("Admin Login", "PASS", admin_login_msg)
        results["admin"]["passed"] += 1
        results["admin"]["tests"].append(("Admin Login", "PASS", admin_login_msg))
        
        # Test health endpoint
        health_ok, health_msg = test_health_endpoint(admin_session)
        status = "PASS" if health_ok else "FAIL"
        print_test("GET /api/hiring/v2/health", status, health_msg)
        if health_ok:
            results["admin"]["passed"] += 1
        else:
            results["admin"]["failed"] += 1
        results["admin"]["tests"].append(("GET /api/hiring/v2/health", status, health_msg))
        
        # Test pipeline board
        pipeline_ok, pipeline_msg = test_pipeline_board(admin_session)
        status = "PASS" if pipeline_ok else "FAIL"
        print_test("GET /api/jobs/employer/pipeline-board", status, pipeline_msg)
        if pipeline_ok:
            results["admin"]["passed"] += 1
        else:
            results["admin"]["failed"] += 1
        results["admin"]["tests"].append(("GET /api/jobs/employer/pipeline-board", status, pipeline_msg))
        
        # Test SLA alerts
        sla_ok, sla_msg = test_sla_alerts(admin_session)
        status = "PASS" if sla_ok else "FAIL"
        print_test("GET /api/jobs/employer/sla-alerts", status, sla_msg)
        if sla_ok:
            results["admin"]["passed"] += 1
        else:
            results["admin"]["failed"] += 1
        results["admin"]["tests"].append(("GET /api/jobs/employer/sla-alerts", status, sla_msg))
        
        # Test offers
        offers_ok, offers_msg = test_offers(admin_session)
        status = "PASS" if offers_ok else "FAIL"
        print_test("GET /api/jobs/employer/offers", status, offers_msg)
        if offers_ok:
            results["admin"]["passed"] += 1
        else:
            results["admin"]["failed"] += 1
        results["admin"]["tests"].append(("GET /api/jobs/employer/offers", status, offers_msg))
        
        # Test purge endpoint
        purge_ok, purge_msg = test_purge_endpoint(admin_session)
        status = "PASS" if purge_ok else "FAIL"
        print_test("POST /api/jobs/save/test_final_purge", status, purge_msg)
        if purge_ok:
            results["admin"]["passed"] += 1
        else:
            results["admin"]["failed"] += 1
        results["admin"]["tests"].append(("POST /api/jobs/save/test_final_purge", status, purge_msg))
    else:
        print_test("Admin Login", "FAIL", admin_login_msg)
        results["admin"]["failed"] += 1
        results["admin"]["tests"].append(("Admin Login", "FAIL", admin_login_msg))
    
    # Test with Employer
    print_header("Testing with Employer User")
    employer_session, employer_login_ok, employer_login_msg = login(EMPLOYER_CREDS, "employer")
    
    if employer_login_ok:
        print_test("Employer Login", "PASS", employer_login_msg)
        results["employer"]["passed"] += 1
        results["employer"]["tests"].append(("Employer Login", "PASS", employer_login_msg))
        
        # Test health endpoint
        health_ok, health_msg = test_health_endpoint(employer_session)
        status = "PASS" if health_ok else "FAIL"
        print_test("GET /api/hiring/v2/health", status, health_msg)
        if health_ok:
            results["employer"]["passed"] += 1
        else:
            results["employer"]["failed"] += 1
        results["employer"]["tests"].append(("GET /api/hiring/v2/health", status, health_msg))
        
        # Test pipeline board
        pipeline_ok, pipeline_msg = test_pipeline_board(employer_session)
        status = "PASS" if pipeline_ok else "FAIL"
        print_test("GET /api/jobs/employer/pipeline-board", status, pipeline_msg)
        if pipeline_ok:
            results["employer"]["passed"] += 1
        else:
            results["employer"]["failed"] += 1
        results["employer"]["tests"].append(("GET /api/jobs/employer/pipeline-board", status, pipeline_msg))
        
        # Test SLA alerts
        sla_ok, sla_msg = test_sla_alerts(employer_session)
        status = "PASS" if sla_ok else "FAIL"
        print_test("GET /api/jobs/employer/sla-alerts", status, sla_msg)
        if sla_ok:
            results["employer"]["passed"] += 1
        else:
            results["employer"]["failed"] += 1
        results["employer"]["tests"].append(("GET /api/jobs/employer/sla-alerts", status, sla_msg))
        
        # Test offers
        offers_ok, offers_msg = test_offers(employer_session)
        status = "PASS" if offers_ok else "FAIL"
        print_test("GET /api/jobs/employer/offers", status, offers_msg)
        if offers_ok:
            results["employer"]["passed"] += 1
        else:
            results["employer"]["failed"] += 1
        results["employer"]["tests"].append(("GET /api/jobs/employer/offers", status, offers_msg))
        
        # Test purge endpoint
        purge_ok, purge_msg = test_purge_endpoint(employer_session)
        status = "PASS" if purge_ok else "FAIL"
        print_test("POST /api/jobs/save/test_final_purge", status, purge_msg)
        if purge_ok:
            results["employer"]["passed"] += 1
        else:
            results["employer"]["failed"] += 1
        results["employer"]["tests"].append(("POST /api/jobs/save/test_final_purge", status, purge_msg))
    else:
        print_test("Employer Login", "FAIL", employer_login_msg)
        results["employer"]["failed"] += 1
        results["employer"]["tests"].append(("Employer Login", "FAIL", employer_login_msg))
    
    # Summary
    print_header("Test Summary")
    
    total_passed = results["admin"]["passed"] + results["employer"]["passed"]
    total_failed = results["admin"]["failed"] + results["employer"]["failed"]
    total_tests = total_passed + total_failed
    
    print(f"Admin Tests:    {results['admin']['passed']} passed, {results['admin']['failed']} failed")
    print(f"Employer Tests: {results['employer']['passed']} passed, {results['employer']['failed']} failed")
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_failed > 0:
        print(f"\n{Colors.RED}❌ FAILED: {total_failed} test(s) failed{Colors.RESET}")
        
        # Print failed tests
        print(f"\n{Colors.RED}Failed Tests:{Colors.RESET}")
        for user_type in ["admin", "employer"]:
            for test_name, status, details in results[user_type]["tests"]:
                if status == "FAIL":
                    print(f"  - [{user_type.upper()}] {test_name}: {details}")
        
        sys.exit(1)
    else:
        print(f"\n{Colors.GREEN}✅ SUCCESS: All tests passed{Colors.RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()
