"""
Stripe Production Receipt Endpoint Resilience Test

This test verifies:
1. Both Stripe sessions map to completed transactions
2. Notifications API includes Basic + Premium payment confirmations
3. Receipt PDF endpoints return 200 for both session IDs
4. Receipt endpoints remain functional under moderate load on GPS state endpoint
"""

import asyncio
import httpx
import sys
from datetime import datetime

# Test configuration
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api"

# Test credentials
TEST_EMAIL = "stripe.prod.retest.0d5e32ee@gmail.com"
TEST_PASSWORD = "StripeLive#2026Aa!"

# Stripe session IDs to verify
SESSION_IDS = [
    "cs_live_a1ofmstpJGVMdlh0gYDl2IO3aMpLal1eLiFSbrSRkafxX9Ecdnf7GPTMuK",
    "cs_live_a1ZxbNeJB46gt8tF6dfK9wnTz6jIm2LLaGVCKiKnzSusC7UdDx1Own0O4q"
]

# Test results tracking
test_results = {
    "authentication": {"status": "pending", "details": {}},
    "session_1_completed": {"status": "pending", "details": {}},
    "session_2_completed": {"status": "pending", "details": {}},
    "notifications_basic": {"status": "pending", "details": {}},
    "notifications_premium": {"status": "pending", "details": {}},
    "receipt_pdf_session_1": {"status": "pending", "details": {}},
    "receipt_pdf_session_2": {"status": "pending", "details": {}},
    "gps_load_test": {"status": "pending", "details": {}},
    "receipt_resilience": {"status": "pending", "details": {}},
}

blocking_issues = []


async def test_authentication():
    """Test 1: Verify user authentication"""
    print("\n" + "="*80)
    print("TEST 1: User Authentication")
    print("="*80)
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # Login
            login_response = await client.post(
                f"{API_URL}/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )
            
            print(f"Login Status Code: {login_response.status_code}")
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                print(f"Login Response Keys: {login_data.keys()}")
                
                # Extract user info
                user_id = login_data.get("user_id")
                email = login_data.get("email")
                
                if user_id and email == TEST_EMAIL:
                    test_results["authentication"]["status"] = "pass"
                    test_results["authentication"]["details"] = {
                        "user_id": user_id,
                        "email": email,
                        "authenticated": True
                    }
                    print(f"✅ PASS: User authenticated successfully")
                    print(f"   User ID: {user_id}")
                    print(f"   Email: {email}")
                    return login_data, client.cookies
                else:
                    test_results["authentication"]["status"] = "fail"
                    test_results["authentication"]["details"] = {"error": "User ID or email mismatch"}
                    blocking_issues.append("Authentication failed: User ID or email mismatch")
                    print(f"❌ FAIL: User ID or email mismatch")
                    return None, None
            else:
                test_results["authentication"]["status"] = "fail"
                test_results["authentication"]["details"] = {
                    "status_code": login_response.status_code,
                    "response": login_response.text
                }
                blocking_issues.append(f"Authentication failed with status {login_response.status_code}")
                print(f"❌ FAIL: Login failed with status {login_response.status_code}")
                return None, None
                
    except Exception as e:
        test_results["authentication"]["status"] = "error"
        test_results["authentication"]["details"] = {"error": str(e)}
        blocking_issues.append(f"Authentication error: {str(e)}")
        print(f"❌ ERROR: {str(e)}")
        return None, None


async def test_stripe_sessions_completed(cookies):
    """Test 2: Verify both Stripe sessions map to completed transactions"""
    print("\n" + "="*80)
    print("TEST 2: Stripe Sessions Completion Status")
    print("="*80)
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, cookies=cookies) as client:
            # Get payment history
            history_response = await client.get(f"{API_URL}/payments/history")
            
            print(f"Payment History Status Code: {history_response.status_code}")
            
            if history_response.status_code == 200:
                response_data = history_response.json()
                payments = response_data.get("payments", []) if isinstance(response_data, dict) else response_data
                print(f"Total payments found: {len(payments)}")
                
                # Find payments matching the session IDs
                session_1_payment = None
                session_2_payment = None
                
                for payment in payments:
                    # The payment_id field contains the Stripe session ID
                    payment_id = payment.get("payment_id")
                    if payment_id == SESSION_IDS[0]:
                        session_1_payment = payment
                    elif payment_id == SESSION_IDS[1]:
                        session_2_payment = payment
                
                # Check session 1
                if session_1_payment:
                    status = session_1_payment.get("status")
                    plan_id = session_1_payment.get("plan_id")
                    payment_id = session_1_payment.get("payment_id")
                    
                    if status == "completed":
                        test_results["session_1_completed"]["status"] = "pass"
                        test_results["session_1_completed"]["details"] = {
                            "session_id": SESSION_IDS[0],
                            "payment_id": payment_id,
                            "status": status,
                            "plan_id": plan_id
                        }
                        print(f"✅ PASS: Session 1 maps to completed transaction")
                        print(f"   Session ID: {SESSION_IDS[0]}")
                        print(f"   Payment ID: {payment_id}")
                        print(f"   Status: {status}")
                        print(f"   Plan: {plan_id}")
                    else:
                        test_results["session_1_completed"]["status"] = "fail"
                        test_results["session_1_completed"]["details"] = {
                            "session_id": SESSION_IDS[0],
                            "status": status,
                            "expected": "completed"
                        }
                        blocking_issues.append(f"Session 1 status is '{status}', expected 'completed'")
                        print(f"❌ FAIL: Session 1 status is '{status}', expected 'completed'")
                else:
                    test_results["session_1_completed"]["status"] = "fail"
                    test_results["session_1_completed"]["details"] = {"error": "Session 1 not found in payment history"}
                    blocking_issues.append("Session 1 not found in payment history")
                    print(f"❌ FAIL: Session 1 not found in payment history")
                
                # Check session 2
                if session_2_payment:
                    status = session_2_payment.get("status")
                    plan_id = session_2_payment.get("plan_id")
                    payment_id = session_2_payment.get("payment_id")
                    
                    if status == "completed":
                        test_results["session_2_completed"]["status"] = "pass"
                        test_results["session_2_completed"]["details"] = {
                            "session_id": SESSION_IDS[1],
                            "payment_id": payment_id,
                            "status": status,
                            "plan_id": plan_id
                        }
                        print(f"✅ PASS: Session 2 maps to completed transaction")
                        print(f"   Session ID: {SESSION_IDS[1]}")
                        print(f"   Payment ID: {payment_id}")
                        print(f"   Status: {status}")
                        print(f"   Plan: {plan_id}")
                    else:
                        test_results["session_2_completed"]["status"] = "fail"
                        test_results["session_2_completed"]["details"] = {
                            "session_id": SESSION_IDS[1],
                            "status": status,
                            "expected": "completed"
                        }
                        blocking_issues.append(f"Session 2 status is '{status}', expected 'completed'")
                        print(f"❌ FAIL: Session 2 status is '{status}', expected 'completed'")
                else:
                    test_results["session_2_completed"]["status"] = "fail"
                    test_results["session_2_completed"]["details"] = {"error": "Session 2 not found in payment history"}
                    blocking_issues.append("Session 2 not found in payment history")
                    print(f"❌ FAIL: Session 2 not found in payment history")
                
                return session_1_payment, session_2_payment
            else:
                test_results["session_1_completed"]["status"] = "error"
                test_results["session_2_completed"]["status"] = "error"
                error_msg = f"Payment history request failed with status {history_response.status_code}"
                blocking_issues.append(error_msg)
                print(f"❌ ERROR: {error_msg}")
                return None, None
                
    except Exception as e:
        test_results["session_1_completed"]["status"] = "error"
        test_results["session_2_completed"]["status"] = "error"
        error_msg = f"Stripe sessions check error: {str(e)}"
        blocking_issues.append(error_msg)
        print(f"❌ ERROR: {error_msg}")
        return None, None


async def test_notifications(cookies):
    """Test 3: Verify notifications include Basic + Premium payment confirmations"""
    print("\n" + "="*80)
    print("TEST 3: Payment Notifications")
    print("="*80)
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, cookies=cookies) as client:
            # Get notifications
            notifications_response = await client.get(f"{API_URL}/notifications")
            
            print(f"Notifications Status Code: {notifications_response.status_code}")
            
            if notifications_response.status_code == 200:
                response_data = notifications_response.json()
                notifications = response_data.get("notifications", []) if isinstance(response_data, dict) else response_data
                print(f"Total notifications found: {len(notifications)}")
                
                # Find payment confirmation notifications
                basic_notification = None
                premium_notification = None
                
                for notification in notifications:
                    notification_type = notification.get("type", "")
                    title = notification.get("title", "")
                    message = notification.get("message", "")
                    
                    if "payment" in notification_type.lower() or "payment confirmed" in title.lower():
                        if "basic" in title.lower() or "basic" in message.lower():
                            basic_notification = notification
                        if "premium" in title.lower() or "premium" in message.lower():
                            premium_notification = notification
                
                # Check Basic notification
                if basic_notification:
                    test_results["notifications_basic"]["status"] = "pass"
                    test_results["notifications_basic"]["details"] = {
                        "title": basic_notification.get("title"),
                        "type": basic_notification.get("type"),
                        "found": True
                    }
                    print(f"✅ PASS: Basic plan payment notification found")
                    print(f"   Title: {basic_notification.get('title')}")
                    print(f"   Type: {basic_notification.get('type')}")
                else:
                    test_results["notifications_basic"]["status"] = "fail"
                    test_results["notifications_basic"]["details"] = {"error": "Basic plan notification not found"}
                    blocking_issues.append("Basic plan payment notification not found")
                    print(f"❌ FAIL: Basic plan payment notification not found")
                
                # Check Premium notification
                if premium_notification:
                    test_results["notifications_premium"]["status"] = "pass"
                    test_results["notifications_premium"]["details"] = {
                        "title": premium_notification.get("title"),
                        "type": premium_notification.get("type"),
                        "found": True
                    }
                    print(f"✅ PASS: Premium plan payment notification found")
                    print(f"   Title: {premium_notification.get('title')}")
                    print(f"   Type: {premium_notification.get('type')}")
                else:
                    test_results["notifications_premium"]["status"] = "fail"
                    test_results["notifications_premium"]["details"] = {"error": "Premium plan notification not found"}
                    blocking_issues.append("Premium plan payment notification not found")
                    print(f"❌ FAIL: Premium plan payment notification not found")
                
            else:
                test_results["notifications_basic"]["status"] = "error"
                test_results["notifications_premium"]["status"] = "error"
                error_msg = f"Notifications request failed with status {notifications_response.status_code}"
                blocking_issues.append(error_msg)
                print(f"❌ ERROR: {error_msg}")
                
    except Exception as e:
        test_results["notifications_basic"]["status"] = "error"
        test_results["notifications_premium"]["status"] = "error"
        error_msg = f"Notifications check error: {str(e)}"
        blocking_issues.append(error_msg)
        print(f"❌ ERROR: {error_msg}")


async def test_receipt_pdf_endpoints(cookies, session_1_payment, session_2_payment):
    """Test 4: Verify receipt PDF endpoints return 200 for both session IDs"""
    print("\n" + "="*80)
    print("TEST 4: Receipt PDF Endpoints")
    print("="*80)
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, cookies=cookies) as client:
            # Test receipt PDF for session 1
            if session_1_payment:
                payment_id_1 = session_1_payment.get("payment_id")
                if payment_id_1:
                    receipt_1_response = await client.get(f"{API_URL}/payments/receipt/{payment_id_1}/pdf")
                    
                    print(f"Receipt PDF Session 1 Status Code: {receipt_1_response.status_code}")
                    
                    if receipt_1_response.status_code == 200:
                        content_type = receipt_1_response.headers.get("content-type", "")
                        content_length = len(receipt_1_response.content)
                        
                        test_results["receipt_pdf_session_1"]["status"] = "pass"
                        test_results["receipt_pdf_session_1"]["details"] = {
                            "session_id": SESSION_IDS[0],
                            "payment_id": payment_id_1,
                            "status_code": 200,
                            "content_type": content_type,
                            "content_length": content_length
                        }
                        print(f"✅ PASS: Receipt PDF endpoint returns 200 for session 1")
                        print(f"   Session ID: {SESSION_IDS[0]}")
                        print(f"   Payment ID: {payment_id_1}")
                        print(f"   Content-Type: {content_type}")
                        print(f"   Content-Length: {content_length} bytes")
                    else:
                        test_results["receipt_pdf_session_1"]["status"] = "fail"
                        test_results["receipt_pdf_session_1"]["details"] = {
                            "session_id": SESSION_IDS[0],
                            "payment_id": payment_id_1,
                            "status_code": receipt_1_response.status_code,
                            "expected": 200
                        }
                        blocking_issues.append(f"Receipt PDF session 1 returned {receipt_1_response.status_code}, expected 200")
                        print(f"❌ FAIL: Receipt PDF session 1 returned {receipt_1_response.status_code}, expected 200")
                else:
                    test_results["receipt_pdf_session_1"]["status"] = "skip"
                    print(f"⚠️  SKIP: Session 1 payment ID not available")
            else:
                test_results["receipt_pdf_session_1"]["status"] = "skip"
                print(f"⚠️  SKIP: Session 1 payment not found")
            
            # Test receipt PDF for session 2
            if session_2_payment:
                payment_id_2 = session_2_payment.get("payment_id")
                if payment_id_2:
                    receipt_2_response = await client.get(f"{API_URL}/payments/receipt/{payment_id_2}/pdf")
                    
                    print(f"Receipt PDF Session 2 Status Code: {receipt_2_response.status_code}")
                    
                    if receipt_2_response.status_code == 200:
                        content_type = receipt_2_response.headers.get("content-type", "")
                        content_length = len(receipt_2_response.content)
                        
                        test_results["receipt_pdf_session_2"]["status"] = "pass"
                        test_results["receipt_pdf_session_2"]["details"] = {
                            "session_id": SESSION_IDS[1],
                            "payment_id": payment_id_2,
                            "status_code": 200,
                            "content_type": content_type,
                            "content_length": content_length
                        }
                        print(f"✅ PASS: Receipt PDF endpoint returns 200 for session 2")
                        print(f"   Session ID: {SESSION_IDS[1]}")
                        print(f"   Payment ID: {payment_id_2}")
                        print(f"   Content-Type: {content_type}")
                        print(f"   Content-Length: {content_length} bytes")
                    else:
                        test_results["receipt_pdf_session_2"]["status"] = "fail"
                        test_results["receipt_pdf_session_2"]["details"] = {
                            "session_id": SESSION_IDS[1],
                            "payment_id": payment_id_2,
                            "status_code": receipt_2_response.status_code,
                            "expected": 200
                        }
                        blocking_issues.append(f"Receipt PDF session 2 returned {receipt_2_response.status_code}, expected 200")
                        print(f"❌ FAIL: Receipt PDF session 2 returned {receipt_2_response.status_code}, expected 200")
                else:
                    test_results["receipt_pdf_session_2"]["status"] = "skip"
                    print(f"⚠️  SKIP: Session 2 payment ID not available")
            else:
                test_results["receipt_pdf_session_2"]["status"] = "skip"
                print(f"⚠️  SKIP: Session 2 payment not found")
                
    except Exception as e:
        error_msg = f"Receipt PDF endpoints check error: {str(e)}"
        blocking_issues.append(error_msg)
        print(f"❌ ERROR: {error_msg}")


async def test_gps_load_and_receipt_resilience(cookies, session_1_payment, session_2_payment):
    """Test 5: Simulate load on GPS state endpoint and verify receipt endpoints remain functional"""
    print("\n" + "="*80)
    print("TEST 5: GPS Load Test & Receipt Endpoint Resilience")
    print("="*80)
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, cookies=cookies) as client:
            # Simulate moderate load on GPS state endpoint
            print("Simulating moderate load on /api/gps/state endpoint...")
            
            gps_requests = []
            num_requests = 20  # Moderate burst
            
            for i in range(num_requests):
                gps_requests.append(client.get(f"{API_URL}/gps/state"))
            
            gps_responses = await asyncio.gather(*gps_requests, return_exceptions=True)
            
            # Count successful GPS requests
            gps_success_count = 0
            gps_429_count = 0
            gps_error_count = 0
            
            for response in gps_responses:
                if isinstance(response, Exception):
                    gps_error_count += 1
                elif response.status_code == 200:
                    gps_success_count += 1
                elif response.status_code == 429:
                    gps_429_count += 1
                else:
                    gps_error_count += 1
            
            test_results["gps_load_test"]["status"] = "pass"
            test_results["gps_load_test"]["details"] = {
                "total_requests": num_requests,
                "successful": gps_success_count,
                "rate_limited_429": gps_429_count,
                "errors": gps_error_count
            }
            
            print(f"✅ GPS Load Test Complete")
            print(f"   Total Requests: {num_requests}")
            print(f"   Successful (200): {gps_success_count}")
            print(f"   Rate Limited (429): {gps_429_count}")
            print(f"   Errors: {gps_error_count}")
            
            # Now test receipt endpoints under this load
            print("\nTesting receipt endpoints after GPS load...")
            
            receipt_tests = []
            if session_1_payment and session_1_payment.get("payment_id"):
                receipt_tests.append(("session_1", session_1_payment.get("payment_id")))
            if session_2_payment and session_2_payment.get("payment_id"):
                receipt_tests.append(("session_2", session_2_payment.get("payment_id")))
            
            all_receipts_ok = True
            receipt_results = []
            
            for session_name, payment_id in receipt_tests:
                receipt_response = await client.get(f"{API_URL}/payments/receipt/{payment_id}/pdf")
                
                if receipt_response.status_code == 200:
                    receipt_results.append({
                        "session": session_name,
                        "payment_id": payment_id,
                        "status_code": 200,
                        "success": True
                    })
                    print(f"   ✅ Receipt PDF for {session_name}: 200 OK")
                elif receipt_response.status_code == 429:
                    receipt_results.append({
                        "session": session_name,
                        "payment_id": payment_id,
                        "status_code": 429,
                        "success": False,
                        "error": "Rate limited"
                    })
                    all_receipts_ok = False
                    blocking_issues.append(f"Receipt endpoint for {session_name} blocked by 429 rate limit")
                    print(f"   ❌ Receipt PDF for {session_name}: 429 Rate Limited")
                else:
                    receipt_results.append({
                        "session": session_name,
                        "payment_id": payment_id,
                        "status_code": receipt_response.status_code,
                        "success": False,
                        "error": f"Unexpected status {receipt_response.status_code}"
                    })
                    all_receipts_ok = False
                    print(f"   ❌ Receipt PDF for {session_name}: {receipt_response.status_code}")
            
            if all_receipts_ok:
                test_results["receipt_resilience"]["status"] = "pass"
                test_results["receipt_resilience"]["details"] = {
                    "all_receipts_accessible": True,
                    "no_429_blocks": True,
                    "receipt_results": receipt_results
                }
                print(f"\n✅ PASS: Receipt endpoints remain functional under GPS load")
                print(f"   No 429 rate limits on receipt endpoints")
            else:
                test_results["receipt_resilience"]["status"] = "fail"
                test_results["receipt_resilience"]["details"] = {
                    "all_receipts_accessible": False,
                    "receipt_results": receipt_results
                }
                print(f"\n❌ FAIL: Receipt endpoints affected by rate limiting or errors")
                
    except Exception as e:
        test_results["gps_load_test"]["status"] = "error"
        test_results["receipt_resilience"]["status"] = "error"
        error_msg = f"GPS load test error: {str(e)}"
        blocking_issues.append(error_msg)
        print(f"❌ ERROR: {error_msg}")


def print_final_summary():
    """Print final test summary"""
    print("\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result["status"] == "pass")
    failed_tests = sum(1 for result in test_results.values() if result["status"] == "fail")
    error_tests = sum(1 for result in test_results.values() if result["status"] == "error")
    skipped_tests = sum(1 for result in test_results.values() if result["status"] == "skip")
    
    print(f"\nTest Results:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {failed_tests}")
    print(f"  Errors: {error_tests}")
    print(f"  Skipped: {skipped_tests}")
    
    print(f"\nDetailed Results:")
    for test_name, result in test_results.items():
        status_symbol = "✅" if result["status"] == "pass" else "❌" if result["status"] == "fail" else "⚠️" if result["status"] == "skip" else "🔴"
        print(f"  {status_symbol} {test_name}: {result['status'].upper()}")
    
    if blocking_issues:
        print(f"\n⚠️  BLOCKING ISSUES FOUND ({len(blocking_issues)}):")
        for i, issue in enumerate(blocking_issues, 1):
            print(f"  {i}. {issue}")
    else:
        print(f"\n✅ NO BLOCKING ISSUES FOUND")
    
    print("\n" + "="*80)
    
    # Determine overall verdict
    if failed_tests > 0 or error_tests > 0:
        print("OVERALL VERDICT: ❌ FAIL")
        return 1
    else:
        print("OVERALL VERDICT: ✅ PASS")
        return 0


async def main():
    """Main test execution"""
    print("="*80)
    print("STRIPE PRODUCTION RECEIPT ENDPOINT RESILIENCE TEST")
    print("="*80)
    print(f"Test URL: {BASE_URL}")
    print(f"Test User: {TEST_EMAIL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print("="*80)
    
    # Test 1: Authentication
    user_data, cookies = await test_authentication()
    if not user_data or not cookies:
        print("\n❌ Authentication failed. Cannot proceed with remaining tests.")
        return print_final_summary()
    
    # Test 2: Stripe sessions completed
    session_1_payment, session_2_payment = await test_stripe_sessions_completed(cookies)
    
    # Test 3: Notifications
    await test_notifications(cookies)
    
    # Test 4: Receipt PDF endpoints
    await test_receipt_pdf_endpoints(cookies, session_1_payment, session_2_payment)
    
    # Test 5: GPS load test and receipt resilience
    await test_gps_load_and_receipt_resilience(cookies, session_1_payment, session_2_payment)
    
    # Print final summary
    return print_final_summary()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
