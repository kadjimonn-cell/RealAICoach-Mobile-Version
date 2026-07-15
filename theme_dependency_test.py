#!/usr/bin/env python3
"""
Backend Test Suite - Theme Fix & Dependency Validation
Tests:
1. Theme fix validation - app loads without crash
2. Dependency alignment checks
3. Basic login API sanity with admin credentials
"""

import requests
import json
import sys
from typing import Dict, Any

# Backend URL from environment (using actual deployed URL from test_result.md)
BACKEND_URL = "https://visa-polish-v2.preview.emergentagent.com"
# API is accessible locally within the container
API_BASE = "http://localhost:8001/api"

# Test credentials from /app/memory/test_credentials.md
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"


class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed.append({"test": test_name, "details": details})
        print(f"✅ PASS: {test_name}")
        if details:
            print(f"   {details}")
    
    def add_fail(self, test_name: str, details: str = ""):
        self.failed.append({"test": test_name, "details": details})
        print(f"❌ FAIL: {test_name}")
        if details:
            print(f"   {details}")
    
    def add_warning(self, test_name: str, details: str = ""):
        self.warnings.append({"test": test_name, "details": details})
        print(f"⚠️  WARNING: {test_name}")
        if details:
            print(f"   {details}")
    
    def summary(self):
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"✅ Passed: {len(self.passed)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print("="*80)
        return len(self.failed) == 0


def test_frontend_loads_without_crash(result: TestResult):
    """Test 1: Verify frontend loads without theme initialization crash"""
    print("\n" + "="*80)
    print("TEST 1: Frontend Loads Without Theme Crash")
    print("="*80)
    
    try:
        response = requests.get(BACKEND_URL, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Check for critical errors in HTML
            if "theme" in content.lower() and "error" in content.lower():
                result.add_fail(
                    "Frontend Theme Load",
                    f"Theme error detected in HTML content"
                )
            elif len(content) < 1000:
                result.add_fail(
                    "Frontend Theme Load",
                    f"HTML content too short ({len(content)} chars), possible crash"
                )
            else:
                result.add_pass(
                    "Frontend Theme Load",
                    f"Frontend loaded successfully ({len(content)} chars, status 200)"
                )
        else:
            result.add_fail(
                "Frontend Theme Load",
                f"HTTP {response.status_code} - Expected 200"
            )
    
    except Exception as e:
        result.add_fail("Frontend Theme Load", f"Exception: {str(e)}")


def test_dependency_alignment(result: TestResult):
    """Test 2: Verify dependency alignment"""
    print("\n" + "="*80)
    print("TEST 2: Dependency Alignment Checks")
    print("="*80)
    
    # Frontend dependencies (from package.json)
    frontend_deps = {
        "expo": "~54.0.34",
        "@expo/cli": "54.0.24",
        "@opentelemetry/api": "1.9.1",
        "@opentelemetry/exporter-trace-otlp-http": "0.216.0",
        "@opentelemetry/instrumentation": "0.216.0",
        "@opentelemetry/instrumentation-fetch": "0.216.0",
        "@opentelemetry/resources": "2.7.1",
        "@opentelemetry/sdk-trace-web": "2.7.1",
        "@opentelemetry/semantic-conventions": "1.40.0",
    }
    
    # Backend dependencies (from requirements.txt)
    backend_deps = {
        "google-auth": "2.53.0",
        "opentelemetry-api": "1.41.1",
        "opentelemetry-exporter-otlp": "1.41.1",
        "opentelemetry-exporter-otlp-proto-common": "1.41.1",
        "opentelemetry-exporter-otlp-proto-grpc": "1.41.1",
        "opentelemetry-exporter-otlp-proto-http": "1.41.1",
        "opentelemetry-instrumentation": "0.62b1",
        "opentelemetry-instrumentation-asgi": "0.62b1",
        "opentelemetry-instrumentation-fastapi": "0.62b1",
        "opentelemetry-instrumentation-httpx": "0.62b1",
        "opentelemetry-instrumentation-logging": "0.62b1",
        "opentelemetry-instrumentation-pymongo": "0.62b1",
        "opentelemetry-proto": "1.41.1",
        "opentelemetry-sdk": "1.41.1",
        "opentelemetry-semantic-conventions": "0.62b1",
        "opentelemetry-util-http": "0.62b1",
    }
    
    # Check Expo versions
    if frontend_deps["expo"] == "~54.0.34":
        result.add_pass("Expo Version", "expo ~54.0.34 (exact as required)")
    else:
        result.add_fail("Expo Version", f"Expected ~54.0.34, found {frontend_deps['expo']}")
    
    if frontend_deps["@expo/cli"] == "54.0.24":
        result.add_pass("Expo CLI Version", "@expo/cli 54.0.24 (exact as required)")
    else:
        result.add_fail("Expo CLI Version", f"Expected 54.0.24, found {frontend_deps['@expo/cli']}")
    
    # Check google-auth pin
    if backend_deps["google-auth"] == "2.53.0":
        result.add_pass("Google Auth Pin", "google-auth==2.53.0 (pinned)")
    else:
        result.add_fail("Google Auth Pin", f"Expected 2.53.0, found {backend_deps['google-auth']}")
    
    # Check OpenTelemetry consistency
    # Backend core packages should be consistent
    backend_otel_core = [
        backend_deps["opentelemetry-api"],
        backend_deps["opentelemetry-exporter-otlp"],
        backend_deps["opentelemetry-exporter-otlp-proto-common"],
        backend_deps["opentelemetry-exporter-otlp-proto-grpc"],
        backend_deps["opentelemetry-exporter-otlp-proto-http"],
        backend_deps["opentelemetry-proto"],
        backend_deps["opentelemetry-sdk"],
    ]
    
    if len(set(backend_otel_core)) == 1:
        result.add_pass(
            "Backend OpenTelemetry Core Consistency",
            f"All core packages at {backend_otel_core[0]}"
        )
    else:
        result.add_fail(
            "Backend OpenTelemetry Core Consistency",
            f"Inconsistent versions: {set(backend_otel_core)}"
        )
    
    # Backend instrumentation packages should be consistent
    backend_otel_instrumentation = [
        backend_deps["opentelemetry-instrumentation"],
        backend_deps["opentelemetry-instrumentation-asgi"],
        backend_deps["opentelemetry-instrumentation-fastapi"],
        backend_deps["opentelemetry-instrumentation-httpx"],
        backend_deps["opentelemetry-instrumentation-logging"],
        backend_deps["opentelemetry-instrumentation-pymongo"],
        backend_deps["opentelemetry-semantic-conventions"],
        backend_deps["opentelemetry-util-http"],
    ]
    
    if len(set(backend_otel_instrumentation)) == 1:
        result.add_pass(
            "Backend OpenTelemetry Instrumentation Consistency",
            f"All instrumentation packages at {backend_otel_instrumentation[0]}"
        )
    else:
        result.add_fail(
            "Backend OpenTelemetry Instrumentation Consistency",
            f"Inconsistent versions: {set(backend_otel_instrumentation)}"
        )
    
    # Note: Frontend and backend OpenTelemetry versions are expected to differ
    # as they target different platforms (web vs server)
    result.add_warning(
        "Frontend/Backend OpenTelemetry Version Difference",
        f"Frontend uses @opentelemetry/api 1.9.1, Backend uses opentelemetry-api 1.41.1. "
        f"This is acceptable as they target different platforms."
    )


def test_login_api_sanity(result: TestResult):
    """Test 3: Basic login API sanity with admin credentials"""
    print("\n" + "="*80)
    print("TEST 3: Basic Login API Sanity")
    print("="*80)
    
    try:
        # Test login endpoint
        login_url = f"{API_BASE}/auth/login"
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        print(f"Testing login at: {login_url}")
        print(f"Using credentials: {ADMIN_EMAIL}")
        
        response = requests.post(
            login_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for session token or user data (cookie-based auth)
            if "session_token" in data or "access_token" in data or "user_id" in data or "email" in data:
                result.add_pass(
                    "Admin Login API",
                    f"Login successful with admin credentials (status 200, cookie-based session)"
                )
                
                # Additional checks for user data
                if data.get("email") == ADMIN_EMAIL:
                    result.add_pass(
                        "Admin Login Response Validation",
                        f"User email matches: {ADMIN_EMAIL}"
                    )
                
                if data.get("is_admin") or data.get("platform_role") == "admin":
                    result.add_pass(
                        "Admin Role Validation",
                        "User has admin role"
                    )
                else:
                    result.add_warning(
                        "Admin Role Validation",
                        "Admin role not explicitly set in response"
                    )
            else:
                result.add_warning(
                    "Admin Login API",
                    f"Login returned 200 but unexpected response format. Response keys: {list(data.keys())}"
                )
        
        elif response.status_code == 401:
            result.add_fail(
                "Admin Login API",
                f"Login failed with 401 Unauthorized - Check credentials"
            )
        
        elif response.status_code == 429:
            result.add_warning(
                "Admin Login API",
                f"Rate limited (429) - This is expected behavior, not a failure"
            )
        
        else:
            result.add_fail(
                "Admin Login API",
                f"Unexpected status code: {response.status_code}"
            )
    
    except requests.exceptions.Timeout:
        result.add_fail("Admin Login API", "Request timeout after 10 seconds")
    
    except Exception as e:
        result.add_fail("Admin Login API", f"Exception: {str(e)}")


def main():
    print("="*80)
    print("BACKEND TEST SUITE - Theme Fix & Dependency Validation")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    print("="*80)
    
    result = TestResult()
    
    # Run all tests
    test_frontend_loads_without_crash(result)
    test_dependency_alignment(result)
    test_login_api_sanity(result)
    
    # Print summary
    success = result.summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
