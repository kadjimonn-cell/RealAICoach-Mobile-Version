"""Feature 31 Tier Entitlement Regression Test - Root-Cause Patch Verification

Strict checks:
1) /api/ai-solver/context-sources plan values by role:
   - free => free
   - basic => basic
   - admin => premium
2) Same exact plan mapping for /api/ai-problem-solver/context-sources
3) Same mapping in bootstrap context for both prefixes.
4) Ensure policy differs across tiers (daily_limit and max_tasks not identical between free/basic/premium).
5) admin control-plane ACL still holds: free/basic 403, admin 200.

Return concise pass/fail with matrix evidence.
"""

import requests
import json
from typing import Dict, Any, Optional, List, Tuple

# Base URL
BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"

# Test credentials
CREDENTIALS = {
    "free": {"email": "p1.free.1779113329@example.com", "password": "P1Free#2026!Aa"},
    "basic": {"email": "f21.basic.1781338672@example.com", "password": "F21Basic#2026Aa"},
    "admin": {"email": "admin@realaicoach.app", "password": "NewAdminPass2026!"}
}

# Expected plan mapping
EXPECTED_PLAN_MAPPING = {
    "free": "free",
    "basic": "basic",
    "admin": "premium"
}

# Test results storage
results = []


def create_session(role: str) -> Optional[requests.Session]:
    """Create authenticated session for a user role."""
    creds = CREDENTIALS[role]
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    })
    
    try:
        resp = session.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=10)
        if resp.status_code == 200:
            print(f"✅ Login successful for {role} user ({creds['email']})")
            return session
        else:
            print(f"❌ Login failed for {role} user: {resp.status_code} - {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Login exception for {role} user: {e}")
        return None


def test_context_sources(session: requests.Session, role: str, endpoint: str) -> Tuple[bool, str, Any]:
    """Test context-sources endpoint and validate plan value."""
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = session.get(url, timeout=10)
        status = resp.status_code
        
        if status != 200:
            return False, f"Status {status} (expected 200)", None
        
        try:
            data = resp.json()
        except:
            return False, "Invalid JSON response", None
        
        # Extract plan value
        plan = data.get("plan")
        expected_plan = EXPECTED_PLAN_MAPPING[role]
        
        if plan == expected_plan:
            return True, f"plan={plan} (correct)", data
        else:
            return False, f"plan={plan} (expected {expected_plan})", data
            
    except Exception as e:
        return False, f"Exception: {e}", None


def test_bootstrap_context(session: requests.Session, role: str, endpoint: str) -> Tuple[bool, str, Any]:
    """Test bootstrap endpoint and validate context plan value."""
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = session.get(url, timeout=10)
        status = resp.status_code
        
        if status != 200:
            return False, f"Status {status} (expected 200)", None
        
        try:
            data = resp.json()
        except:
            return False, "Invalid JSON response", None
        
        # Extract plan from context
        context = data.get("context", {})
        plan = context.get("plan")
        expected_plan = EXPECTED_PLAN_MAPPING[role]
        
        if plan == expected_plan:
            return True, f"context.plan={plan} (correct)", data
        else:
            return False, f"context.plan={plan} (expected {expected_plan})", data
            
    except Exception as e:
        return False, f"Exception: {e}", None


def test_admin_control_plane(session: requests.Session, role: str) -> Tuple[bool, str]:
    """Test admin control-plane ACL."""
    url = f"{BASE_URL}/api/ai-problem-solver/admin/control-plane"
    expected_status = 403 if role in ["free", "basic"] else 200
    
    try:
        resp = session.get(url, timeout=10)
        status = resp.status_code
        
        if status == expected_status:
            return True, f"Status {status} (correct)"
        else:
            return False, f"Status {status} (expected {expected_status})"
            
    except Exception as e:
        return False, f"Exception: {e}"


def extract_policy_limits(data: Any) -> Dict[str, Any]:
    """Extract policy limits from response data."""
    if not isinstance(data, dict):
        return {}
    
    result = {}
    
    # Try plan_policy first (most common location)
    plan_policy = data.get("plan_policy", {})
    if plan_policy:
        result["daily_limit"] = plan_policy.get("daily_limit")
        result["max_tasks"] = plan_policy.get("max_tasks")
        return result
    
    # Try other locations
    policy = data.get("policy", {})
    limits = data.get("limits", {})
    context = data.get("context", {})
    
    # Extract daily_limit
    if "daily_limit" in policy:
        result["daily_limit"] = policy["daily_limit"]
    elif "daily_limit" in limits:
        result["daily_limit"] = limits["daily_limit"]
    elif "daily_limit" in context:
        result["daily_limit"] = context["daily_limit"]
    
    # Extract max_tasks
    if "max_tasks" in policy:
        result["max_tasks"] = policy["max_tasks"]
    elif "max_tasks" in limits:
        result["max_tasks"] = limits["max_tasks"]
    elif "max_tasks" in context:
        result["max_tasks"] = context["max_tasks"]
    
    return result


def run_tier_entitlement_tests():
    """Run all tier entitlement validation tests."""
    print("="*120)
    print("FEATURE 31 TIER ENTITLEMENT REGRESSION TEST - ROOT-CAUSE PATCH VERIFICATION")
    print("="*120)
    print(f"Base URL: {BASE_URL}")
    print()
    
    # Create sessions for all roles
    sessions = {}
    for role in ["free", "basic", "admin"]:
        sessions[role] = create_session(role)
        if not sessions[role]:
            print(f"⚠️  WARNING: Could not create session for {role} user")
    
    print()
    print("="*120)
    print("TEST 1: /api/ai-solver/context-sources - Plan Value Validation")
    print("="*120)
    
    ai_solver_policies = {}
    for role in ["free", "basic", "admin"]:
        if sessions[role]:
            success, msg, data = test_context_sources(sessions[role], role, "/api/ai-solver/context-sources")
            icon = "✅" if success else "❌"
            print(f"  {icon} {role:6s} | {msg}")
            
            # Extract policy limits
            if data:
                ai_solver_policies[role] = extract_policy_limits(data)
            
            results.append({
                "test": "ai-solver/context-sources plan",
                "role": role,
                "expected": EXPECTED_PLAN_MAPPING[role],
                "result": msg,
                "passed": success
            })
    
    print()
    print("="*120)
    print("TEST 2: /api/ai-problem-solver/context-sources - Plan Value Validation")
    print("="*120)
    
    ai_problem_solver_policies = {}
    for role in ["free", "basic", "admin"]:
        if sessions[role]:
            success, msg, data = test_context_sources(sessions[role], role, "/api/ai-problem-solver/context-sources")
            icon = "✅" if success else "❌"
            print(f"  {icon} {role:6s} | {msg}")
            
            # Extract policy limits
            if data:
                ai_problem_solver_policies[role] = extract_policy_limits(data)
            
            results.append({
                "test": "ai-problem-solver/context-sources plan",
                "role": role,
                "expected": EXPECTED_PLAN_MAPPING[role],
                "result": msg,
                "passed": success
            })
    
    print()
    print("="*120)
    print("TEST 3: /api/ai-solver/bootstrap - Context Plan Validation")
    print("="*120)
    
    for role in ["free", "basic", "admin"]:
        if sessions[role]:
            success, msg, data = test_bootstrap_context(sessions[role], role, "/api/ai-solver/bootstrap")
            icon = "✅" if success else "❌"
            print(f"  {icon} {role:6s} | {msg}")
            
            results.append({
                "test": "ai-solver/bootstrap context.plan",
                "role": role,
                "expected": EXPECTED_PLAN_MAPPING[role],
                "result": msg,
                "passed": success
            })
    
    print()
    print("="*120)
    print("TEST 4: /api/ai-problem-solver/bootstrap - Context Plan Validation")
    print("="*120)
    
    for role in ["free", "basic", "admin"]:
        if sessions[role]:
            success, msg, data = test_bootstrap_context(sessions[role], role, "/api/ai-problem-solver/bootstrap")
            icon = "✅" if success else "❌"
            print(f"  {icon} {role:6s} | {msg}")
            
            results.append({
                "test": "ai-problem-solver/bootstrap context.plan",
                "role": role,
                "expected": EXPECTED_PLAN_MAPPING[role],
                "result": msg,
                "passed": success
            })
    
    print()
    print("="*120)
    print("TEST 5: Admin Control-Plane ACL Validation")
    print("="*120)
    
    for role in ["free", "basic", "admin"]:
        if sessions[role]:
            success, msg = test_admin_control_plane(sessions[role], role)
            icon = "✅" if success else "❌"
            expected = "403" if role in ["free", "basic"] else "200"
            print(f"  {icon} {role:6s} | {msg} (expected {expected})")
            
            results.append({
                "test": "admin/control-plane ACL",
                "role": role,
                "expected": expected,
                "result": msg,
                "passed": success
            })
    
    print()
    print("="*120)
    print("TEST 6: Policy Limits Differentiation Across Tiers")
    print("="*120)
    
    # Check ai-solver policies
    print("\n  ai-solver/context-sources policies:")
    for role in ["free", "basic", "admin"]:
        if role in ai_solver_policies:
            policy = ai_solver_policies[role]
            print(f"    {role:6s} | daily_limit: {policy.get('daily_limit', 'N/A'):>10} | max_tasks: {policy.get('max_tasks', 'N/A'):>10}")
    
    # Check ai-problem-solver policies
    print("\n  ai-problem-solver/context-sources policies:")
    for role in ["free", "basic", "admin"]:
        if role in ai_problem_solver_policies:
            policy = ai_problem_solver_policies[role]
            print(f"    {role:6s} | daily_limit: {policy.get('daily_limit', 'N/A'):>10} | max_tasks: {policy.get('max_tasks', 'N/A'):>10}")
    
    # Validate that policies differ across tiers
    print("\n  Policy Differentiation Check:")
    
    # Check ai-solver
    ai_solver_unique = len(set(str(ai_solver_policies.get(r, {})) for r in ["free", "basic", "admin"])) > 1
    icon1 = "✅" if ai_solver_unique else "❌"
    print(f"    {icon1} ai-solver policies differ across tiers: {ai_solver_unique}")
    
    # Check ai-problem-solver
    ai_problem_solver_unique = len(set(str(ai_problem_solver_policies.get(r, {})) for r in ["free", "basic", "admin"])) > 1
    icon2 = "✅" if ai_problem_solver_unique else "❌"
    print(f"    {icon2} ai-problem-solver policies differ across tiers: {ai_problem_solver_unique}")
    
    results.append({
        "test": "Policy differentiation",
        "role": "all",
        "expected": "Policies differ across tiers",
        "result": f"ai-solver: {ai_solver_unique}, ai-problem-solver: {ai_problem_solver_unique}",
        "passed": ai_solver_unique and ai_problem_solver_unique
    })
    
    print()


def print_summary_matrix():
    """Print concise pass/fail matrix."""
    print("="*120)
    print("SUMMARY MATRIX - FEATURE 31 TIER ENTITLEMENT REGRESSION")
    print("="*120)
    print()
    
    # Group by test type
    test_groups = {}
    for result in results:
        test = result["test"]
        if test not in test_groups:
            test_groups[test] = []
        test_groups[test].append(result)
    
    # Print matrix
    print(f"{'Test':<50} | {'Role':<6} | {'Expected':<20} | {'Result':<40} | {'Status':<6}")
    print("-" * 130)
    
    for test, test_results in test_groups.items():
        for i, result in enumerate(test_results):
            test_name = test if i == 0 else ""
            role = result["role"]
            expected = result["expected"]
            res = result["result"]
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            
            print(f"{test_name:<50} | {role:<6} | {expected:<20} | {res:<40} | {status:<6}")
    
    print()
    
    # Calculate totals
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    
    print("="*120)
    print("FINAL VERDICT")
    print("="*120)
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print()
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - Feature 31 tier entitlement regression fixed!")
    else:
        print("⚠️  SOME TESTS FAILED - Tier entitlement regression still present")
    
    print("="*120)


def main():
    """Main entry point."""
    run_tier_entitlement_tests()
    print_summary_matrix()


if __name__ == "__main__":
    main()
