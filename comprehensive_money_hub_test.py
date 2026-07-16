"""
Comprehensive backend testing for Feature 9 (Money Strategy Hub)
Testing all endpoints with focus on:
- No Mongo _id/ObjectId serialization leaks
- Tier usage/limits shape in bootstrap
- Budget spent/remaining reacts to expense create/delete
- AI endpoints return structured payloads
"""

import os
import requests
import json
import base64
from datetime import datetime, timezone, timedelta

BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest"
})

results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": [],
    "critical_bugs": []
}

state = {
    "budget_id": None,
    "expense_id": None,
    "goal_id": None,
    "bill_id": None,
    "position_id": None,
}


def log_test(name: str, ok: bool, detail: str = "", critical: bool = False):
    results["total"] += 1
    if ok:
        results["passed"] += 1
        print(f"✅ PASS: {name}")
        if detail:
            print(f"   {detail}")
    else:
        results["failed"] += 1
        error_msg = f"{name}: {detail}"
        results["errors"].append(error_msg)
        if critical:
            results["critical_bugs"].append(error_msg)
        print(f"❌ FAIL: {name}")
        if detail:
            print(f"   {detail}")


def check_no_mongo_id(data: dict, path: str = "root") -> tuple[bool, str]:
    """Recursively check for _id or ObjectId in response"""
    if isinstance(data, dict):
        if "_id" in data:
            return False, f"Found '_id' field at {path}"
        for key, value in data.items():
            ok, msg = check_no_mongo_id(value, f"{path}.{key}")
            if not ok:
                return False, msg
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            ok, msg = check_no_mongo_id(item, f"{path}[{idx}]")
            if not ok:
                return False, msg
    return True, ""


def login():
    print("\n=== AUTHENTICATION ===")
    resp = session.post(
        f"{API_BASE}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if resp.status_code != 200:
        log_test("Login", False, f"status={resp.status_code}", critical=True)
        return False
    log_test("Login", True, "Admin authenticated")
    return True


def test_bootstrap():
    print("\n=== BOOTSTRAP ENDPOINT ===")
    resp = session.get(f"{API_BASE}/money-strategy-hub/bootstrap")
    if resp.status_code != 200:
        log_test("Bootstrap GET", False, f"status={resp.status_code}", critical=True)
        return
    
    log_test("Bootstrap GET", True, "200 OK")
    
    data = resp.json()
    
    # Check no _id leaks
    ok, msg = check_no_mongo_id(data)
    log_test("Bootstrap: No _id leaks", ok, msg if not ok else "Clean response", critical=not ok)
    
    # Check tier/usage/limits shape
    required_keys = ["tier", "usage", "active", "features", "tier_limits"]
    has_all = all(k in data for k in required_keys)
    log_test("Bootstrap: Required keys present", has_all, 
             f"Missing: {[k for k in required_keys if k not in data]}" if not has_all else "All present")
    
    # Check usage shape
    usage_keys = ["budgets_this_month", "expenses_today", "goals_this_month", 
                  "receipt_scans_this_month", "advisor_runs_this_month"]
    usage_ok = all(k in data.get("usage", {}) for k in usage_keys)
    log_test("Bootstrap: Usage shape correct", usage_ok,
             f"Usage keys: {list(data.get('usage', {}).keys())}")
    
    # Check tier_limits shape
    tier = data.get("tier", "unknown")
    limits = data.get("tier_limits", {})
    limit_keys = ["budgets_per_month", "expenses_per_day", "savings_goals_per_month",
                  "bill_reminders_active", "portfolio_positions", "receipt_scans_per_month",
                  "advisor_runs_per_month", "features"]
    limits_ok = all(k in limits for k in limit_keys)
    log_test("Bootstrap: Tier limits shape correct", limits_ok,
             f"Tier: {tier}, Limit keys: {list(limits.keys())}")
    
    print(f"   Tier: {tier}")
    print(f"   Usage: {data.get('usage')}")
    print(f"   Active: {data.get('active')}")


def test_profile_crud():
    print("\n=== PROFILE CRUD ===")
    
    # Create/Upsert
    create_payload = {
        "currency": "USD",
        "monthly_income": 8500,
        "fixed_monthly_expenses": 3100,
        "savings_target_monthly": 1800,
        "risk_tolerance": "moderate",
        "investment_horizon_years": 5,
        "financial_goals": ["Emergency fund", "ETF accumulation"]
    }
    resp = session.post(f"{API_BASE}/money-strategy-hub/profile", json=create_payload)
    if resp.status_code != 200:
        log_test("Profile POST", False, f"status={resp.status_code}", critical=True)
        return
    
    log_test("Profile POST", True, "200 OK")
    data = resp.json()
    ok, msg = check_no_mongo_id(data)
    log_test("Profile POST: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    # Get
    resp = session.get(f"{API_BASE}/money-strategy-hub/profile")
    if resp.status_code != 200:
        log_test("Profile GET", False, f"status={resp.status_code}")
        return
    
    log_test("Profile GET", True, "200 OK")
    data = resp.json()
    ok, msg = check_no_mongo_id(data)
    log_test("Profile GET: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    # Update
    update_payload = {"monthly_income": 9000, "savings_target_monthly": 2200}
    resp = session.put(f"{API_BASE}/money-strategy-hub/profile", json=update_payload)
    if resp.status_code != 200:
        log_test("Profile PUT", False, f"status={resp.status_code}")
        return
    
    log_test("Profile PUT", True, "200 OK")
    data = resp.json()
    ok, msg = check_no_mongo_id(data)
    log_test("Profile PUT: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)


def test_budget_expense_interaction():
    print("\n=== BUDGET + EXPENSE INTERACTION ===")
    
    # Create budget
    budget_payload = {
        "name": "Test Budget",
        "category": "groceries",
        "monthly_limit": 500.00
    }
    resp = session.post(f"{API_BASE}/money-strategy-hub/budgets", json=budget_payload)
    if resp.status_code != 200:
        log_test("Budget CREATE", False, f"status={resp.status_code}", critical=True)
        return
    
    log_test("Budget CREATE", True, "200 OK")
    budget = resp.json().get("budget", {})
    state["budget_id"] = budget.get("budget_id")
    
    ok, msg = check_no_mongo_id(budget)
    log_test("Budget CREATE: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    initial_spent = budget.get("spent_amount", 0)
    initial_remaining = budget.get("remaining_amount", 0)
    monthly_limit = budget.get("monthly_limit", 0)
    
    print(f"   Initial: spent={initial_spent}, remaining={initial_remaining}, limit={monthly_limit}")
    
    # Create expense linked to budget
    expense_payload = {
        "amount": 145.75,
        "category": "groceries",
        "merchant": "Test Store",
        "budget_id": state["budget_id"],
        "payment_method": "card"
    }
    resp = session.post(f"{API_BASE}/money-strategy-hub/expenses", json=expense_payload)
    if resp.status_code != 200:
        log_test("Expense CREATE (with budget_id)", False, f"status={resp.status_code}", critical=True)
        return
    
    log_test("Expense CREATE (with budget_id)", True, "200 OK")
    expense = resp.json().get("expense", {})
    state["expense_id"] = expense.get("expense_id")
    expense_amount = expense.get("amount", 0)
    
    ok, msg = check_no_mongo_id(expense)
    log_test("Expense CREATE: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    # Get budget again to check if spent/remaining updated
    resp = session.get(f"{API_BASE}/money-strategy-hub/budgets")
    if resp.status_code != 200:
        log_test("Budget GET after expense", False, f"status={resp.status_code}")
        return
    
    budgets = resp.json().get("budgets", [])
    updated_budget = next((b for b in budgets if b.get("budget_id") == state["budget_id"]), None)
    
    if not updated_budget:
        log_test("Budget spent/remaining update", False, "Budget not found after expense", critical=True)
        return
    
    new_spent = updated_budget.get("spent_amount", 0)
    new_remaining = updated_budget.get("remaining_amount", 0)
    
    print(f"   After expense: spent={new_spent}, remaining={new_remaining}")
    
    # Verify spent increased by expense amount
    expected_spent = round(initial_spent + expense_amount, 2)
    spent_correct = abs(new_spent - expected_spent) < 0.01
    log_test("Budget spent increased correctly", spent_correct,
             f"Expected: {expected_spent}, Got: {new_spent}", critical=not spent_correct)
    
    # Verify remaining decreased
    expected_remaining = round(monthly_limit - new_spent, 2)
    remaining_correct = abs(new_remaining - expected_remaining) < 0.01
    log_test("Budget remaining decreased correctly", remaining_correct,
             f"Expected: {expected_remaining}, Got: {new_remaining}", critical=not remaining_correct)
    
    # Delete expense and verify budget updates
    resp = session.delete(f"{API_BASE}/money-strategy-hub/expenses/{state['expense_id']}")
    if resp.status_code != 200:
        log_test("Expense DELETE", False, f"status={resp.status_code}")
        return
    
    log_test("Expense DELETE", True, "200 OK")
    
    # Get budget again
    resp = session.get(f"{API_BASE}/money-strategy-hub/budgets")
    budgets = resp.json().get("budgets", [])
    final_budget = next((b for b in budgets if b.get("budget_id") == state["budget_id"]), None)
    
    if final_budget:
        final_spent = final_budget.get("spent_amount", 0)
        final_remaining = final_budget.get("remaining_amount", 0)
        
        print(f"   After delete: spent={final_spent}, remaining={final_remaining}")
        
        # Verify spent decreased back
        spent_reverted = abs(final_spent - initial_spent) < 0.01
        log_test("Budget spent reverted after expense delete", spent_reverted,
                 f"Expected: {initial_spent}, Got: {final_spent}", critical=not spent_reverted)
        
        remaining_reverted = abs(final_remaining - initial_remaining) < 0.01
        log_test("Budget remaining reverted after expense delete", remaining_reverted,
                 f"Expected: {initial_remaining}, Got: {final_remaining}", critical=not remaining_reverted)


def test_expense_analytics():
    print("\n=== EXPENSE ANALYTICS ===")
    
    resp = session.get(f"{API_BASE}/money-strategy-hub/expenses/analytics")
    if resp.status_code != 200:
        log_test("Expense analytics GET", False, f"status={resp.status_code}")
        return
    
    log_test("Expense analytics GET", True, "200 OK")
    data = resp.json()
    
    ok, msg = check_no_mongo_id(data)
    log_test("Expense analytics: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    # Check structure
    required_keys = ["period_days", "summary", "top_categories", "daily_trend"]
    has_all = all(k in data for k in required_keys)
    log_test("Expense analytics: Structure correct", has_all,
             f"Keys: {list(data.keys())}")
    
    summary = data.get("summary", {})
    summary_keys = ["total_spent", "transaction_count", "avg_ticket"]
    summary_ok = all(k in summary for k in summary_keys)
    log_test("Expense analytics: Summary shape correct", summary_ok,
             f"Summary: {summary}")


def test_savings_goals():
    print("\n=== SAVINGS GOALS ===")
    
    # Create
    goal_payload = {
        "title": "Test Goal",
        "target_amount": 5000,
        "current_amount": 1200,
        "priority": "high"
    }
    resp = session.post(f"{API_BASE}/money-strategy-hub/savings-goals", json=goal_payload)
    if resp.status_code != 200:
        log_test("Savings goal CREATE", False, f"status={resp.status_code}")
        return
    
    log_test("Savings goal CREATE", True, "200 OK")
    goal = resp.json().get("goal", {})
    state["goal_id"] = goal.get("goal_id")
    
    ok, msg = check_no_mongo_id(goal)
    log_test("Savings goal CREATE: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    # List
    resp = session.get(f"{API_BASE}/money-strategy-hub/savings-goals")
    if resp.status_code != 200:
        log_test("Savings goals GET", False, f"status={resp.status_code}")
        return
    
    log_test("Savings goals GET", True, "200 OK")
    data = resp.json()
    
    ok, msg = check_no_mongo_id(data)
    log_test("Savings goals GET: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    # Update
    update_payload = {"current_amount": 2500}
    resp = session.put(f"{API_BASE}/money-strategy-hub/savings-goals/{state['goal_id']}", json=update_payload)
    if resp.status_code != 200:
        log_test("Savings goal PUT", False, f"status={resp.status_code}")
        return
    
    log_test("Savings goal PUT", True, "200 OK")
    data = resp.json()
    
    ok, msg = check_no_mongo_id(data)
    log_test("Savings goal PUT: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)


def test_bill_reminders():
    print("\n=== BILL REMINDERS ===")
    
    # Create
    due_date = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
    bill_payload = {
        "title": "Test Bill",
        "amount_due": 99.99,
        "due_date": due_date,
        "category": "utilities"
    }
    resp = session.post(f"{API_BASE}/money-strategy-hub/bill-reminders", json=bill_payload)
    if resp.status_code != 200:
        log_test("Bill reminder CREATE", False, f"status={resp.status_code}")
        return
    
    log_test("Bill reminder CREATE", True, "200 OK")
    bill = resp.json().get("bill_reminder", {})
    state["bill_id"] = bill.get("reminder_id")
    
    ok, msg = check_no_mongo_id(bill)
    log_test("Bill reminder CREATE: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    # List
    resp = session.get(f"{API_BASE}/money-strategy-hub/bill-reminders")
    if resp.status_code != 200:
        log_test("Bill reminders GET", False, f"status={resp.status_code}")
        return
    
    log_test("Bill reminders GET", True, "200 OK")
    data = resp.json()
    
    ok, msg = check_no_mongo_id(data)
    log_test("Bill reminders GET: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    # Update
    update_payload = {"status": "paid"}
    resp = session.put(f"{API_BASE}/money-strategy-hub/bill-reminders/{state['bill_id']}", json=update_payload)
    if resp.status_code != 200:
        log_test("Bill reminder PUT", False, f"status={resp.status_code}")
        return
    
    log_test("Bill reminder PUT", True, "200 OK")
    data = resp.json()
    
    ok, msg = check_no_mongo_id(data)
    log_test("Bill reminder PUT: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)


def test_portfolio():
    print("\n=== PORTFOLIO POSITIONS ===")
    
    # Create
    position_payload = {
        "asset_type": "stock",
        "symbol": "AAPL",
        "quantity": 10,
        "average_cost": 150.00,
        "current_price": 175.00
    }
    resp = session.post(f"{API_BASE}/money-strategy-hub/portfolio/positions", json=position_payload)
    if resp.status_code != 200:
        log_test("Portfolio position CREATE", False, f"status={resp.status_code}")
        return
    
    log_test("Portfolio position CREATE", True, "200 OK")
    position = resp.json().get("position", {})
    state["position_id"] = position.get("position_id")
    
    ok, msg = check_no_mongo_id(position)
    log_test("Portfolio position CREATE: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    # List
    resp = session.get(f"{API_BASE}/money-strategy-hub/portfolio/positions")
    if resp.status_code != 200:
        log_test("Portfolio positions GET", False, f"status={resp.status_code}")
        return
    
    log_test("Portfolio positions GET", True, "200 OK")
    data = resp.json()
    
    ok, msg = check_no_mongo_id(data)
    log_test("Portfolio positions GET: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    # Update
    update_payload = {"current_price": 180.00}
    resp = session.put(f"{API_BASE}/money-strategy-hub/portfolio/positions/{state['position_id']}", json=update_payload)
    if resp.status_code != 200:
        log_test("Portfolio position PUT", False, f"status={resp.status_code}")
        return
    
    log_test("Portfolio position PUT", True, "200 OK")
    data = resp.json()
    
    ok, msg = check_no_mongo_id(data)
    log_test("Portfolio position PUT: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    # Analytics
    resp = session.get(f"{API_BASE}/money-strategy-hub/portfolio/analytics")
    if resp.status_code != 200:
        log_test("Portfolio analytics GET", False, f"status={resp.status_code}")
        return
    
    log_test("Portfolio analytics GET", True, "200 OK")
    data = resp.json()
    
    ok, msg = check_no_mongo_id(data)
    log_test("Portfolio analytics: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    # Check structure
    required_keys = ["summary", "allocation"]
    has_all = all(k in data for k in required_keys)
    log_test("Portfolio analytics: Structure correct", has_all,
             f"Keys: {list(data.keys())}")
    
    summary = data.get("summary", {})
    summary_keys = ["positions_count", "total_market_value", "total_cost_basis", "unrealized_pnl", "roi_pct"]
    summary_ok = all(k in summary for k in summary_keys)
    log_test("Portfolio analytics: Summary shape correct", summary_ok,
             f"Summary: {summary}")


def test_receipt_scan():
    print("\n=== RECEIPT SCAN (AI) ===")
    
    # Create a small valid PNG image (2x2 red square)
    png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFElEQVR4nGP8z8Dwn4GBgYGJAQoAHxcCAr7mDbQAAAAASUVORK5CYII="
    
    receipt_payload = {
        "image_base64": png_base64,
        "notes": "Test receipt"
    }
    resp = session.post(f"{API_BASE}/money-strategy-hub/receipt-scan", json=receipt_payload)
    if resp.status_code != 200:
        log_test("Receipt scan POST", False, f"status={resp.status_code}")
        return
    
    log_test("Receipt scan POST", True, "200 OK")
    data = resp.json()
    
    ok, msg = check_no_mongo_id(data)
    log_test("Receipt scan: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    # Check structure
    required_keys = ["scan", "expense_draft"]
    has_all = all(k in data for k in required_keys)
    log_test("Receipt scan: Structure correct", has_all,
             f"Keys: {list(data.keys())}")
    
    scan = data.get("scan", {})
    scan_keys = ["scan_id", "owner_id", "extracted_data", "created_at"]
    scan_ok = all(k in scan for k in scan_keys)
    log_test("Receipt scan: Scan shape correct", scan_ok,
             f"Scan keys: {list(scan.keys())}")
    
    extracted = scan.get("extracted_data", {})
    extracted_keys = ["merchant", "total_amount", "currency", "transaction_date", 
                      "category_suggestion", "payment_method", "confidence"]
    extracted_ok = all(k in extracted for k in extracted_keys)
    log_test("Receipt scan: Extracted data shape correct", extracted_ok,
             f"Extracted: {extracted}")
    
    draft = data.get("expense_draft", {})
    draft_keys = ["amount", "category", "merchant", "transaction_date", "payment_method", "currency", "source"]
    draft_ok = all(k in draft for k in draft_keys)
    log_test("Receipt scan: Expense draft shape correct", draft_ok,
             f"Draft: {draft}")


def test_ai_advisor():
    print("\n=== AI ADVISOR ===")
    
    advisor_payload = {
        "question": "How can I optimize my budget?",
        "planning_horizon_months": 6,
        "include_investment": True
    }
    resp = session.post(f"{API_BASE}/money-strategy-hub/ai-advisor", json=advisor_payload)
    if resp.status_code != 200:
        log_test("AI advisor POST", False, f"status={resp.status_code}")
        return
    
    log_test("AI advisor POST", True, "200 OK")
    data = resp.json()
    
    ok, msg = check_no_mongo_id(data)
    log_test("AI advisor: No _id leaks", ok, msg if not ok else "Clean", critical=not ok)
    
    # Check structure
    required_keys = ["run", "context_snapshot"]
    has_all = all(k in data for k in required_keys)
    log_test("AI advisor: Structure correct", has_all,
             f"Keys: {list(data.keys())}")
    
    run = data.get("run", {})
    run_keys = ["run_id", "owner_id", "question", "planning_horizon_months", "include_investment", "advice", "created_at"]
    run_ok = all(k in run for k in run_keys)
    log_test("AI advisor: Run shape correct", run_ok,
             f"Run keys: {list(run.keys())}")
    
    advice = run.get("advice", {})
    advice_keys = ["summary", "risk_score", "monthly_action_plan", "savings_moves", 
                   "debt_moves", "investment_notes", "warnings"]
    advice_ok = all(k in advice for k in advice_keys)
    log_test("AI advisor: Advice shape correct", advice_ok,
             f"Advice keys: {list(advice.keys())}")
    
    # Verify structured payload (not just text)
    is_structured = (
        isinstance(advice.get("monthly_action_plan"), list) and
        isinstance(advice.get("savings_moves"), list) and
        isinstance(advice.get("debt_moves"), list) and
        isinstance(advice.get("investment_notes"), list) and
        isinstance(advice.get("warnings"), list) and
        isinstance(advice.get("risk_score"), int)
    )
    log_test("AI advisor: Structured payload (not plain text)", is_structured,
             f"Advice structure: {advice}", critical=not is_structured)


def cleanup():
    print("\n=== CLEANUP ===")
    
    if state.get("budget_id"):
        resp = session.delete(f"{API_BASE}/money-strategy-hub/budgets/{state['budget_id']}")
        log_test("Cleanup: Budget delete", resp.status_code == 200)


def print_summary():
    print("\n" + "=" * 88)
    print("COMPREHENSIVE BACKEND TEST SUMMARY")
    print("=" * 88)
    print(f"Total:  {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    
    if results["critical_bugs"]:
        print(f"\n🚨 CRITICAL BUGS ({len(results['critical_bugs'])}):")
        for bug in results["critical_bugs"]:
            print(f"  - {bug}")
    
    if results["errors"]:
        print(f"\nAll Errors ({len(results['errors'])}):")
        for err in results["errors"]:
            print(f"  - {err}")
    
    print("=" * 88)
    
    if results["critical_bugs"]:
        print("\n❌ CRITICAL ISSUES FOUND - REQUIRES IMMEDIATE ATTENTION")
        return 1
    elif results["failed"] > 0:
        print("\n⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
        return 1
    else:
        print("\n✅ ALL TESTS PASSED - FEATURE 9 BACKEND VERIFIED")
        return 0


def main():
    if not login():
        return 1
    
    test_bootstrap()
    test_profile_crud()
    test_budget_expense_interaction()
    test_expense_analytics()
    test_savings_goals()
    test_bill_reminders()
    test_portfolio()
    test_receipt_scan()
    test_ai_advisor()
    cleanup()
    
    return print_summary()


if __name__ == "__main__":
    exit(main())
