#!/usr/bin/env python3
"""
Feature 24 Phase-2 Backend Smoke Validation
Specific requirements from review request:
1. Login as free user (p1.free.1779113329@example.com / P1Free#2026!Aa)
2. Verify GET /api/ai-learn/hub-dashboard returns 200
3. Validate response contains:
   - onboarding.total_steps > 0
   - onboarding.steps array
   - weekly_achievement_loop.mission_cards array
   - weekly_achievement_loop.completion_rewards array
   - weekly_achievement_loop.leaderboard_teaser.entries array
4. Verify existing AI learning hub endpoints still healthy (200):
   - GET /api/ai-learn/my-learning-center
   - GET /api/ai-learn/habit-loop/summary
"""

import requests
import json
import sys

BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
FREE_USER_EMAIL = "p1.free.1779113329@example.com"
FREE_USER_PASSWORD = "P1Free#2026!Aa"

def print_header(text):
    print("\n" + "="*80)
    print(text)
    print("="*80)

def print_result(passed, test_name, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"   {details}")

def main():
    print_header("FEATURE 24 PHASE-2 BACKEND SMOKE VALIDATION")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {FREE_USER_EMAIL}")
    
    all_tests_passed = True
    
    # Step 1: Login as free user
    print_header("Step 1: Login as free user")
    session = requests.Session()
    
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": FREE_USER_EMAIL, "password": FREE_USER_PASSWORD},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Login", f"User ID: {data.get('user_id', 'N/A')}, Plan: {data.get('subscription_plan', 'N/A')}")
        else:
            print_result(False, "Login", f"Status: {response.status_code}, Response: {response.text[:200]}")
            all_tests_passed = False
            sys.exit(1)
    except Exception as e:
        print_result(False, "Login", f"Exception: {str(e)}")
        all_tests_passed = False
        sys.exit(1)
    
    # Step 2: Test hub-dashboard endpoint
    print_header("Step 2: GET /api/ai-learn/hub-dashboard")
    
    try:
        response = session.get(
            f"{BASE_URL}/api/ai-learn/hub-dashboard",
            timeout=30
        )
        
        # Check status code
        if response.status_code != 200:
            print_result(False, "hub-dashboard status", f"Expected 200, got {response.status_code}")
            all_tests_passed = False
        else:
            print_result(True, "hub-dashboard status", "200 OK")
            
            # Parse response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                print_result(False, "hub-dashboard JSON", f"Invalid JSON: {str(e)}")
                all_tests_passed = False
                sys.exit(1)
            
            # Validate Phase-2 requirements
            print("\nPhase-2 Requirements Validation:")
            
            # 1. onboarding.total_steps > 0
            onboarding = data.get("onboarding", {})
            total_steps = onboarding.get("total_steps", 0)
            passed = total_steps > 0
            print_result(passed, "onboarding.total_steps > 0", f"total_steps = {total_steps}")
            if not passed:
                all_tests_passed = False
            
            # 2. onboarding.steps array
            steps = onboarding.get("steps", [])
            passed = isinstance(steps, list)
            print_result(passed, "onboarding.steps array", f"{len(steps) if isinstance(steps, list) else 'NOT AN ARRAY'} items")
            if not passed:
                all_tests_passed = False
            
            # 3. weekly_achievement_loop.mission_cards array
            weekly_loop = data.get("weekly_achievement_loop", {})
            mission_cards = weekly_loop.get("mission_cards", [])
            passed = isinstance(mission_cards, list)
            print_result(passed, "weekly_achievement_loop.mission_cards array", f"{len(mission_cards) if isinstance(mission_cards, list) else 'NOT AN ARRAY'} items")
            if not passed:
                all_tests_passed = False
            
            # 4. weekly_achievement_loop.completion_rewards array
            completion_rewards = weekly_loop.get("completion_rewards", [])
            passed = isinstance(completion_rewards, list)
            print_result(passed, "weekly_achievement_loop.completion_rewards array", f"{len(completion_rewards) if isinstance(completion_rewards, list) else 'NOT AN ARRAY'} items")
            if not passed:
                all_tests_passed = False
            
            # 5. weekly_achievement_loop.leaderboard_teaser.entries array
            leaderboard_teaser = weekly_loop.get("leaderboard_teaser", {})
            entries = leaderboard_teaser.get("entries", [])
            passed = isinstance(entries, list)
            print_result(passed, "weekly_achievement_loop.leaderboard_teaser.entries array", f"{len(entries) if isinstance(entries, list) else 'NOT AN ARRAY'} items")
            if not passed:
                all_tests_passed = False
    
    except Exception as e:
        print_result(False, "hub-dashboard", f"Exception: {str(e)}")
        all_tests_passed = False
    
    # Step 3: Test existing endpoints
    print_header("Step 3: Verify existing AI learning hub endpoints")
    
    endpoints = [
        "/api/ai-learn/my-learning-center",
        "/api/ai-learn/habit-loop/summary"
    ]
    
    for endpoint in endpoints:
        try:
            response = session.get(
                f"{BASE_URL}{endpoint}",
                timeout=30
            )
            
            if response.status_code == 200:
                print_result(True, f"GET {endpoint}", "200 OK")
            else:
                print_result(False, f"GET {endpoint}", f"Expected 200, got {response.status_code}")
                all_tests_passed = False
        
        except Exception as e:
            print_result(False, f"GET {endpoint}", f"Exception: {str(e)}")
            all_tests_passed = False
    
    # Final summary
    print_header("FINAL RESULT")
    
    if all_tests_passed:
        print("🟢 PASS - All Feature 24 Phase-2 requirements validated successfully")
        print("\nEndpoint-level evidence:")
        print("  ✅ GET /api/ai-learn/hub-dashboard - 200 OK")
        print("     - onboarding.total_steps > 0: ✅")
        print("     - onboarding.steps array: ✅")
        print("     - weekly_achievement_loop.mission_cards array: ✅")
        print("     - weekly_achievement_loop.completion_rewards array: ✅")
        print("     - weekly_achievement_loop.leaderboard_teaser.entries array: ✅")
        print("  ✅ GET /api/ai-learn/my-learning-center - 200 OK")
        print("  ✅ GET /api/ai-learn/habit-loop/summary - 200 OK")
        sys.exit(0)
    else:
        print("🔴 FAIL - Some Feature 24 Phase-2 requirements failed validation")
        sys.exit(1)

if __name__ == "__main__":
    main()
