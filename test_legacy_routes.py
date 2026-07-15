#!/usr/bin/env python3
"""Quick test for legacy route retirement"""

import requests

BASE_URL = "http://localhost:8001"

# Login as admin
session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest"
})

login_resp = session.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": "admin@realaicoach.app", "password": "NewAdminPass2026!"}
)

print(f"Login status: {login_resp.status_code}")
print(f"Cookies: {session.cookies}")

if login_resp.status_code == 200:
    # Test legacy routes
    print("\n=== Testing Legacy Routes ===")
    
    # Test 1: POST /api/jobs/save/test_migration_1
    resp1 = session.post(f"{BASE_URL}/api/jobs/save/test_migration_1", json={})
    print(f"\nPOST /api/jobs/save/test_migration_1")
    print(f"Status: {resp1.status_code}")
    print(f"Response: {resp1.text[:500]}")
    
    # Test 2: POST /api/employers/reverify
    resp2 = session.post(f"{BASE_URL}/api/employers/reverify", json={})
    print(f"\nPOST /api/employers/reverify")
    print(f"Status: {resp2.status_code}")
    print(f"Response: {resp2.text[:500]}")
