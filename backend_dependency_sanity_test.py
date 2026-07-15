#!/usr/bin/env python3
"""
Backend Dependency Alignment Sanity Test
Tests OpenTelemetry upgrades and backend health after dependency updates.
"""

import sys
import json
import subprocess
import requests

def test_backend_health():
    """Test 1: Backend health endpoint returns 200 JSON"""
    print("=" * 60)
    print("TEST 1: Backend Health Check")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8001/api/health", timeout=5)
        
        if response.status_code != 200:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            return False
        
        # Verify it's valid JSON
        data = response.json()
        
        if not isinstance(data, dict):
            print(f"❌ FAIL: Response is not a JSON object")
            return False
        
        print(f"✅ PASS: GET /api/health returns 200 JSON")
        print(f"   Response: {json.dumps(data, indent=2)}")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_backend_opentelemetry_imports():
    """Test 2: Backend starts without OpenTelemetry import errors"""
    print("\n" + "=" * 60)
    print("TEST 2: Backend OpenTelemetry Import Sanity")
    print("=" * 60)
    
    try:
        # Check installed OpenTelemetry packages
        result = subprocess.run(
            ["pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"❌ FAIL: Could not list installed packages")
            return False
        
        packages = json.loads(result.stdout)
        otel_packages = {
            pkg["name"]: pkg["version"] 
            for pkg in packages 
            if "opentelemetry" in pkg["name"].lower()
        }
        
        # Verify required versions
        required_versions = {
            "opentelemetry-sdk": "1.42.1",
            "opentelemetry-instrumentation": "0.63b1"
        }
        
        all_pass = True
        for pkg_name, expected_version in required_versions.items():
            actual_version = otel_packages.get(pkg_name)
            if actual_version == expected_version:
                print(f"✅ {pkg_name}: {actual_version} (expected: {expected_version})")
            else:
                print(f"❌ {pkg_name}: {actual_version} (expected: {expected_version})")
                all_pass = False
        
        # Check backend logs for import errors
        log_check = subprocess.run(
            ["grep", "-i", "importerror\\|modulenotfounderror", "/var/log/supervisor/backend.err.log"],
            capture_output=True,
            text=True
        )
        
        if log_check.returncode == 0 and log_check.stdout.strip():
            print(f"❌ FAIL: Found import errors in backend logs:")
            print(log_check.stdout[:500])
            return False
        
        print(f"\n✅ PASS: Backend started without OpenTelemetry import errors")
        print(f"   Installed OpenTelemetry packages:")
        for pkg, ver in sorted(otel_packages.items()):
            print(f"   - {pkg}: {ver}")
        
        return all_pass
        
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_frontend_dependencies():
    """Test 3: Frontend package.json has exact dependency pins"""
    print("\n" + "=" * 60)
    print("TEST 3: Frontend Dependency Sanity")
    print("=" * 60)
    
    try:
        with open("/app/frontend/package.json", "r") as f:
            package_json = json.load(f)
        
        dependencies = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
        
        required_versions = {
            "expo": "54.0.34",
            "@expo/cli": "54.0.24",
            "react-native-reanimated": "4.1.1",
            "@opentelemetry/exporter-trace-otlp-http": "0.218.0",
            "@opentelemetry/instrumentation": "0.218.0",
            "@opentelemetry/instrumentation-fetch": "0.218.0",
            "@opentelemetry/semantic-conventions": "1.41.1"
        }
        
        all_pass = True
        for pkg_name, expected_version in required_versions.items():
            actual_version = dependencies.get(pkg_name, "NOT FOUND")
            
            # Handle version ranges (^, ~, etc.)
            actual_clean = actual_version.lstrip("^~>=<")
            
            if actual_version == expected_version or actual_clean == expected_version:
                print(f"✅ {pkg_name}: {actual_version} (expected: {expected_version})")
            else:
                print(f"❌ {pkg_name}: {actual_version} (expected: {expected_version})")
                all_pass = False
        
        if all_pass:
            print(f"\n✅ PASS: All frontend dependencies match exact pins")
        else:
            print(f"\n❌ FAIL: Some frontend dependencies do not match")
        
        return all_pass
        
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def main():
    """Run all sanity tests"""
    print("\n" + "=" * 60)
    print("DEPENDENCY ALIGNMENT SANITY TEST")
    print("Testing OpenTelemetry upgrades and dependency pins")
    print("=" * 60 + "\n")
    
    results = {
        "backend_health": test_backend_health(),
        "backend_opentelemetry": test_backend_opentelemetry_imports(),
        "frontend_dependencies": test_frontend_dependencies()
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
