"""
Feature 22 (Games Station) Backend Regression Test
Tests all bootstrap endpoints with tier-based entitlements and authentication.
"""

import requests
import json
from typing import Dict, Any, List

# Base URL from frontend env
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"

# Test credentials from review request
CREDENTIALS = {
    "free": {"email": "f22.free.20260613@example.com", "password": "F22Free#2026Aa"},
    "basic": {"email": "f22.basic.20260613@example.com", "password": "F22Basic#2026Aa"},
    "premium": {"email": "f22.premium.20260613@example.com", "password": "F22Premium#2026Aa"},
    "admin": {"email": "admin@realaicoach.app", "password": "NewAdminPass2026!"},
}

# Expected 7 game tabs
EXPECTED_TABS = [
    "ai_brain_battle",
    "cyber_runner",
    "meme_madness",
    "space_strike_arena",
    "lucky_chaos_spin",
    "legends_arena",
    "shadow_ops_reborn",
]

# Expected retention_loop fields
EXPECTED_RETENTION_FIELDS = [
    "next_best_tabs",
    "daily_focus",
    "progression_tip",
    "weekly_goal",
    "weekly_progress_xp",
    "weekly_target_xp",
]


class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed.append(f"✅ {test_name}: {details}")
    
    def add_fail(self, test_name: str, details: str):
        self.failed.append(f"❌ {test_name}: {details}")
    
    def add_warning(self, test_name: str, details: str):
        self.warnings.append(f"⚠️  {test_name}: {details}")
    
    def print_summary(self):
        print("\n" + "="*80)
        print("FEATURE 22 (GAMES STATION) BACKEND REGRESSION TEST RESULTS")
        print("="*80)
        
        if self.passed:
            print(f"\n✅ PASSED ({len(self.passed)}):")
            for p in self.passed:
                print(f"  {p}")
        
        if self.failed:
            print(f"\n❌ FAILED ({len(self.failed)}):")
            for f in self.failed:
                print(f"  {f}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"  {w}")
        
        print("\n" + "="*80)
        print(f"SUMMARY: {len(self.passed)} passed, {len(self.failed)} failed, {len(self.warnings)} warnings")
        print("="*80 + "\n")
        
        return len(self.failed) == 0


def login(session: requests.Session, email: str, password: str) -> Dict[str, Any]:
    """Login and return result."""
    try:
        resp = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password},
            timeout=15
        )
        
        if resp.status_code == 200:
            data = resp.json()
            return {
                "success": True,
                "status": 200,
                "data": data,
                "cookies": session.cookies
            }
        else:
            return {
                "success": False,
                "status": resp.status_code,
                "error": resp.text[:200]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def test_login_all_accounts(results: TestResult):
    """Test 1: Login works for all 4 accounts."""
    print("\n[TEST 1] Testing login for all 4 accounts...")
    
    for tier, creds in CREDENTIALS.items():
        session = requests.Session()
        result = login(session, creds["email"], creds["password"])
        
        if result["success"]:
            results.add_pass(
                f"Login {tier}",
                f"{creds['email']} - status {result['status']}"
            )
        else:
            results.add_fail(
                f"Login {tier}",
                f"{creds['email']} - {result.get('error', 'Unknown error')}"
            )


def test_bootstrap_endpoint(results: TestResult):
    """Test 2: /api/games-station/bootstrap returns 200 with correct plan+scope."""
    print("\n[TEST 2] Testing /api/games-station/bootstrap for all tiers...")
    
    expected_plans = {
        "free": {"plan": "free", "scope": "Limited access"},
        "basic": {"plan": "basic", "scope": "Almost unlimited access"},
        "premium": {"plan": "premium", "scope": "Full unlimited access"},
        "admin": {"plan": "premium", "scope": "Full unlimited access"},  # Admin gets premium
    }
    
    for tier, creds in CREDENTIALS.items():
        session = requests.Session()
        login_result = login(session, creds["email"], creds["password"])
        
        if not login_result["success"]:
            results.add_fail(
                f"Bootstrap {tier}",
                f"Login failed: {login_result.get('error', 'Unknown')}"
            )
            continue
        
        try:
            resp = session.get(f"{BASE_URL}/api/games-station/bootstrap", timeout=15)
            
            if resp.status_code != 200:
                results.add_fail(
                    f"Bootstrap {tier}",
                    f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
                )
                continue
            
            data = resp.json()
            actual_plan = data.get("plan", "")
            actual_scope = data.get("scope_label", "")
            expected = expected_plans[tier]
            
            # Check plan and scope
            plan_match = actual_plan == expected["plan"]
            scope_match = actual_scope == expected["scope"]
            
            if plan_match and scope_match:
                results.add_pass(
                    f"Bootstrap {tier}",
                    f"plan={actual_plan}, scope={actual_scope}"
                )
            else:
                details = []
                if not plan_match:
                    details.append(f"plan mismatch: expected {expected['plan']}, got {actual_plan}")
                if not scope_match:
                    details.append(f"scope mismatch: expected {expected['scope']}, got {actual_scope}")
                results.add_fail(
                    f"Bootstrap {tier}",
                    "; ".join(details)
                )
        
        except Exception as e:
            results.add_fail(f"Bootstrap {tier}", f"Exception: {str(e)}")


def test_legends_arena_bootstrap(results: TestResult):
    """Test 3: /api/games-station/legends-arena/bootstrap returns 200 with quota scope."""
    print("\n[TEST 3] Testing /api/games-station/legends-arena/bootstrap...")
    
    for tier, creds in CREDENTIALS.items():
        session = requests.Session()
        login_result = login(session, creds["email"], creds["password"])
        
        if not login_result["success"]:
            results.add_fail(
                f"Legends Arena {tier}",
                f"Login failed: {login_result.get('error', 'Unknown')}"
            )
            continue
        
        try:
            resp = session.get(f"{BASE_URL}/api/games-station/legends-arena/bootstrap", timeout=15)
            
            if resp.status_code != 200:
                results.add_fail(
                    f"Legends Arena {tier}",
                    f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
                )
                continue
            
            data = resp.json()
            
            # Check for quota and scope_label
            quota = data.get("quota", {})
            if not quota:
                results.add_fail(
                    f"Legends Arena {tier}",
                    "Missing 'quota' object in response"
                )
                continue
            
            scope_label = quota.get("scope_label", "")
            if not scope_label:
                results.add_fail(
                    f"Legends Arena {tier}",
                    "Missing 'scope_label' in quota"
                )
                continue
            
            results.add_pass(
                f"Legends Arena {tier}",
                f"scope={scope_label}"
            )
        
        except Exception as e:
            results.add_fail(f"Legends Arena {tier}", f"Exception: {str(e)}")


def test_shadow_ops_bootstrap(results: TestResult):
    """Test 4: /api/games-station/shadow-ops/bootstrap returns 200 with quota scope."""
    print("\n[TEST 4] Testing /api/games-station/shadow-ops/bootstrap...")
    
    for tier, creds in CREDENTIALS.items():
        session = requests.Session()
        login_result = login(session, creds["email"], creds["password"])
        
        if not login_result["success"]:
            results.add_fail(
                f"Shadow Ops {tier}",
                f"Login failed: {login_result.get('error', 'Unknown')}"
            )
            continue
        
        try:
            resp = session.get(f"{BASE_URL}/api/games-station/shadow-ops/bootstrap", timeout=15)
            
            if resp.status_code != 200:
                results.add_fail(
                    f"Shadow Ops {tier}",
                    f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
                )
                continue
            
            data = resp.json()
            
            # Check for quota and scope_label
            quota = data.get("quota", {})
            if not quota:
                results.add_fail(
                    f"Shadow Ops {tier}",
                    "Missing 'quota' object in response"
                )
                continue
            
            scope_label = quota.get("scope_label", "")
            if not scope_label:
                results.add_fail(
                    f"Shadow Ops {tier}",
                    "Missing 'scope_label' in quota"
                )
                continue
            
            results.add_pass(
                f"Shadow Ops {tier}",
                f"scope={scope_label}"
            )
        
        except Exception as e:
            results.add_fail(f"Shadow Ops {tier}", f"Exception: {str(e)}")


def test_bootstrap_tabs(results: TestResult):
    """Test 5: Bootstrap tabs include all 7 expected keys."""
    print("\n[TEST 5] Testing bootstrap tabs include all 7 game keys...")
    
    # Test with admin account
    session = requests.Session()
    login_result = login(session, CREDENTIALS["admin"]["email"], CREDENTIALS["admin"]["password"])
    
    if not login_result["success"]:
        results.add_fail(
            "Bootstrap tabs",
            f"Admin login failed: {login_result.get('error', 'Unknown')}"
        )
        return
    
    try:
        resp = session.get(f"{BASE_URL}/api/games-station/bootstrap", timeout=15)
        
        if resp.status_code != 200:
            results.add_fail(
                "Bootstrap tabs",
                f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
            )
            return
        
        data = resp.json()
        tabs = data.get("tabs", [])
        
        if not tabs:
            results.add_fail("Bootstrap tabs", "No tabs found in response")
            return
        
        tab_keys = [tab.get("game_key") for tab in tabs]
        missing_tabs = [key for key in EXPECTED_TABS if key not in tab_keys]
        extra_tabs = [key for key in tab_keys if key not in EXPECTED_TABS]
        
        if missing_tabs:
            results.add_fail(
                "Bootstrap tabs",
                f"Missing tabs: {', '.join(missing_tabs)}"
            )
        elif extra_tabs:
            results.add_warning(
                "Bootstrap tabs",
                f"Extra tabs found: {', '.join(extra_tabs)}"
            )
            results.add_pass(
                "Bootstrap tabs",
                f"All 7 expected tabs present (found {len(tab_keys)} total)"
            )
        else:
            results.add_pass(
                "Bootstrap tabs",
                f"All 7 tabs present: {', '.join(tab_keys)}"
            )
    
    except Exception as e:
        results.add_fail("Bootstrap tabs", f"Exception: {str(e)}")


def test_retention_loop(results: TestResult):
    """Test 6: retention_loop object fields exist in bootstrap."""
    print("\n[TEST 6] Testing retention_loop object in bootstrap...")
    
    # Test with admin account
    session = requests.Session()
    login_result = login(session, CREDENTIALS["admin"]["email"], CREDENTIALS["admin"]["password"])
    
    if not login_result["success"]:
        results.add_fail(
            "Retention loop",
            f"Admin login failed: {login_result.get('error', 'Unknown')}"
        )
        return
    
    try:
        resp = session.get(f"{BASE_URL}/api/games-station/bootstrap", timeout=15)
        
        if resp.status_code != 200:
            results.add_fail(
                "Retention loop",
                f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
            )
            return
        
        data = resp.json()
        retention_loop = data.get("retention_loop")
        
        if not retention_loop:
            results.add_fail("Retention loop", "retention_loop object missing from bootstrap")
            return
        
        missing_fields = [field for field in EXPECTED_RETENTION_FIELDS if field not in retention_loop]
        
        if missing_fields:
            results.add_fail(
                "Retention loop",
                f"Missing fields: {', '.join(missing_fields)}"
            )
        else:
            results.add_pass(
                "Retention loop",
                f"All {len(EXPECTED_RETENTION_FIELDS)} fields present"
            )
    
    except Exception as e:
        results.add_fail("Retention loop", f"Exception: {str(e)}")


def test_unauthenticated_access(results: TestResult):
    """Test 7: Unauthenticated requests return 401/403."""
    print("\n[TEST 7] Testing unauthenticated access returns 401/403...")
    
    endpoints = [
        "/api/games-station/bootstrap",
        "/api/games-station/legends-arena/bootstrap",
        "/api/games-station/shadow-ops/bootstrap",
    ]
    
    for endpoint in endpoints:
        session = requests.Session()  # Fresh session with no auth
        
        try:
            resp = session.get(f"{BASE_URL}{endpoint}", timeout=15)
            
            if resp.status_code in [401, 403]:
                results.add_pass(
                    f"Unauth {endpoint.split('/')[-2] if 'legends' in endpoint or 'shadow' in endpoint else 'bootstrap'}",
                    f"Correctly returned {resp.status_code}"
                )
            else:
                results.add_fail(
                    f"Unauth {endpoint.split('/')[-2] if 'legends' in endpoint or 'shadow' in endpoint else 'bootstrap'}",
                    f"Expected 401/403, got {resp.status_code}"
                )
        
        except Exception as e:
            results.add_fail(
                f"Unauth {endpoint.split('/')[-2] if 'legends' in endpoint or 'shadow' in endpoint else 'bootstrap'}",
                f"Exception: {str(e)}"
            )


def main():
    """Run all tests."""
    print("="*80)
    print("FEATURE 22 (GAMES STATION) BACKEND REGRESSION TEST")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Testing {len(CREDENTIALS)} user tiers: {', '.join(CREDENTIALS.keys())}")
    print("="*80)
    
    results = TestResult()
    
    # Run all tests
    test_login_all_accounts(results)
    test_bootstrap_endpoint(results)
    test_legends_arena_bootstrap(results)
    test_shadow_ops_bootstrap(results)
    test_bootstrap_tabs(results)
    test_retention_loop(results)
    test_unauthenticated_access(results)
    
    # Print summary
    success = results.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
