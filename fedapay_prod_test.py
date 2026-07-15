"""
FedaPay Production-Readiness Flow Verification Test
Test URL: https://visa-polish-v2.preview.emergentagent.com

Test Flow:
1. Register a new free user and confirm `/api/auth/me` shows free/active
2. Initiate live FedaPay checkout for Basic + Premium via `/api/subscriptions/mobile-money/pay`
3. Simulate provider approval by posting webhook payloads to `/api/payments/fedapay/webhook`
4. Confirm `/api/fedapay/status/{payment_id}` returns completed for both
5. Confirm `/api/notifications` includes payment confirmation notifications
"""

import httpx
import asyncio
import json
import uuid
from datetime import datetime

BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test data
TEST_EMAIL = f"fedapay.prod.test.{int(datetime.now().timestamp())}@example.com"
TEST_PASSWORD = "FedapayProd#2026Aa!"
TEST_NAME = "FedaPay Production Test User"
TEST_PHONE = "+22997000001"  # FedaPay sandbox success number

class TestResults:
    def __init__(self):
        self.results = []
        self.user_id = None
        self.session_token = None
        self.basic_payment_id = None
        self.premium_payment_id = None
        self.basic_tx_id = None
        self.premium_tx_id = None
        self.basic_fedapay_tx_id = None
        self.premium_fedapay_tx_id = None
        
    def add_result(self, test_name, passed, details="", error=None):
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "error": str(error) if error else None,
            "timestamp": datetime.now().isoformat()
        })
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"  Details: {details}")
        if error:
            print(f"  Error: {error}")
    
    def summary(self):
        passed = sum(1 for r in self.results if r["passed"])
        total = len(self.results)
        print(f"\n{'='*80}")
        print(f"TEST SUMMARY: {passed}/{total} tests passed")
        print(f"{'='*80}")
        for r in self.results:
            status = "✅" if r["passed"] else "❌"
            print(f"{status} {r['test']}")
        return passed == total

async def test_production_readiness_flow():
    results = TestResults()
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        
        # ========================================
        # TEST 1: Register new free user
        # ========================================
        try:
            response = await client.post(
                f"{API_BASE}/auth/register",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "name": TEST_NAME
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                results.user_id = data.get("user_id")
                results.session_token = data.get("session_token")
                
                # Extract session token from cookies if not in response
                if not results.session_token:
                    cookies = response.cookies
                    results.session_token = cookies.get("session_token")
                
                results.add_result(
                    "Register new free user",
                    True,
                    f"User ID: {results.user_id}, Email: {TEST_EMAIL}"
                )
            else:
                results.add_result(
                    "Register new free user",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
                return results
        except Exception as e:
            results.add_result("Register new free user", False, error=e)
            return results
        
        # Set auth headers for subsequent requests
        headers = {
            "X-Requested-With": "XMLHttpRequest"  # Required for CSRF validation
        }
        if results.session_token:
            headers["Cookie"] = f"session_token={results.session_token}"
        
        # ========================================
        # TEST 2: Verify /api/auth/me shows free/active
        # ========================================
        try:
            response = await client.get(
                f"{API_BASE}/auth/me",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                subscription_plan = data.get("subscription_plan", "").lower()
                subscription_status = data.get("subscription_status", "").lower()
                
                is_free = subscription_plan in ["free", ""]
                is_active_or_none = subscription_status in ["active", ""]
                
                if is_free:
                    results.add_result(
                        "/api/auth/me shows free plan",
                        True,
                        f"Plan: {subscription_plan or 'free'}, Status: {subscription_status or 'active'}"
                    )
                else:
                    results.add_result(
                        "/api/auth/me shows free plan",
                        False,
                        f"Expected free plan, got: {subscription_plan}"
                    )
            else:
                results.add_result(
                    "/api/auth/me shows free plan",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result("/api/auth/me shows free plan", False, error=e)
        
        # ========================================
        # TEST 3: Initiate FedaPay checkout for Basic plan
        # ========================================
        try:
            response = await client.post(
                f"{API_BASE}/subscriptions/mobile-money/pay",
                json={
                    "plan_id": "basic",
                    "billing_period": "monthly",
                    "gateway": "fedapay",
                    "phone_number": TEST_PHONE,
                    "currency": "XOF",
                    "mobile_provider": "mtn"
                },
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                results.basic_payment_id = data.get("payment_id")
                results.basic_tx_id = data.get("ticket_id")
                
                # Extract fedapay_tx_id from fedapay_reference if available
                results.basic_fedapay_tx_id = data.get("fedapay_reference", "")
                
                results.add_result(
                    "Initiate FedaPay checkout for Basic plan",
                    True,
                    f"Payment ID: {results.basic_payment_id}, Ticket ID: {results.basic_tx_id}, FedaPay TX: {results.basic_fedapay_tx_id}"
                )
            else:
                results.add_result(
                    "Initiate FedaPay checkout for Basic plan",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result("Initiate FedaPay checkout for Basic plan", False, error=e)
        
        # ========================================
        # TEST 4: Initiate FedaPay checkout for Premium plan
        # ========================================
        try:
            response = await client.post(
                f"{API_BASE}/subscriptions/mobile-money/pay",
                json={
                    "plan_id": "premium",
                    "billing_period": "monthly",
                    "gateway": "fedapay",
                    "phone_number": TEST_PHONE,
                    "currency": "XOF",
                    "mobile_provider": "mtn"
                },
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                results.premium_payment_id = data.get("payment_id")
                results.premium_tx_id = data.get("ticket_id")
                
                results.add_result(
                    "Initiate FedaPay checkout for Premium plan",
                    True,
                    f"Payment ID: {results.premium_payment_id}, Ticket ID: {results.premium_tx_id}"
                )
            else:
                results.add_result(
                    "Initiate FedaPay checkout for Premium plan",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result("Initiate FedaPay checkout for Premium plan", False, error=e)
        
        # ========================================
        # TEST 5: Get FedaPay transaction IDs from database
        # ========================================
        # Note: We need to query the payment_transactions collection to get fedapay_tx_id
        # Since we don't have direct DB access in this test, we'll try to get it from the API
        
        # Try to get transaction details if there's an endpoint
        # For now, we'll construct webhook payloads with the payment_ids we have
        
        # ========================================
        # TEST 6: Simulate FedaPay webhook for Basic plan (approved)
        # ========================================
        if results.basic_payment_id and results.basic_tx_id:
            try:
                # Construct FedaPay webhook payload
                webhook_payload = {
                    "name": "transaction.approved",
                    "data": {
                        "entity": {
                            "id": results.basic_tx_id,  # Using ticket_id as transaction ID
                            "status": "approved",
                            "reference": results.basic_tx_id,
                            "amount": 3000,
                            "currency": "XOF"
                        }
                    }
                }
                
                response = await client.post(
                    f"{API_BASE}/payments/fedapay/webhook",
                    json=webhook_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                # Webhook endpoints typically return 200 even if they queue the event
                if response.status_code in [200, 201, 202]:
                    results.add_result(
                        "Simulate FedaPay webhook for Basic plan (approved)",
                        True,
                        f"Webhook accepted, Status: {response.status_code}"
                    )
                else:
                    results.add_result(
                        "Simulate FedaPay webhook for Basic plan (approved)",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                results.add_result("Simulate FedaPay webhook for Basic plan (approved)", False, error=e)
        else:
            results.add_result(
                "Simulate FedaPay webhook for Basic plan (approved)",
                False,
                "Skipped: No Basic payment ID available"
            )
        
        # ========================================
        # TEST 7: Simulate FedaPay webhook for Premium plan (approved)
        # ========================================
        if results.premium_payment_id and results.premium_tx_id:
            try:
                webhook_payload = {
                    "name": "transaction.approved",
                    "data": {
                        "entity": {
                            "id": results.premium_tx_id,
                            "status": "approved",
                            "reference": results.premium_tx_id,
                            "amount": 5000,
                            "currency": "XOF"
                        }
                    }
                }
                
                response = await client.post(
                    f"{API_BASE}/payments/fedapay/webhook",
                    json=webhook_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 201, 202]:
                    results.add_result(
                        "Simulate FedaPay webhook for Premium plan (approved)",
                        True,
                        f"Webhook accepted, Status: {response.status_code}"
                    )
                else:
                    results.add_result(
                        "Simulate FedaPay webhook for Premium plan (approved)",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                results.add_result("Simulate FedaPay webhook for Premium plan (approved)", False, error=e)
        else:
            results.add_result(
                "Simulate FedaPay webhook for Premium plan (approved)",
                False,
                "Skipped: No Premium payment ID available"
            )
        
        # Wait a bit for webhook processing
        await asyncio.sleep(2)
        
        # ========================================
        # TEST 8: Check FedaPay status for Basic payment
        # ========================================
        if results.basic_payment_id:
            try:
                response = await client.get(
                    f"{API_BASE}/fedapay/status/{results.basic_payment_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "").lower()
                    payment_status = data.get("payment_status", "").lower()
                    
                    is_completed = status == "completed" or payment_status == "completed"
                    
                    results.add_result(
                        "/api/fedapay/status/{payment_id} returns completed for Basic",
                        is_completed,
                        f"Status: {status or payment_status}"
                    )
                else:
                    results.add_result(
                        "/api/fedapay/status/{payment_id} returns completed for Basic",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                results.add_result("/api/fedapay/status/{payment_id} returns completed for Basic", False, error=e)
        else:
            results.add_result(
                "/api/fedapay/status/{payment_id} returns completed for Basic",
                False,
                "Skipped: No Basic payment ID available"
            )
        
        # ========================================
        # TEST 9: Check FedaPay status for Premium payment
        # ========================================
        if results.premium_payment_id:
            try:
                response = await client.get(
                    f"{API_BASE}/fedapay/status/{results.premium_payment_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "").lower()
                    payment_status = data.get("payment_status", "").lower()
                    
                    is_completed = status == "completed" or payment_status == "completed"
                    
                    results.add_result(
                        "/api/fedapay/status/{payment_id} returns completed for Premium",
                        is_completed,
                        f"Status: {status or payment_status}"
                    )
                else:
                    results.add_result(
                        "/api/fedapay/status/{payment_id} returns completed for Premium",
                        False,
                        f"Status: {response.status_code}",
                        response.text
                    )
            except Exception as e:
                results.add_result("/api/fedapay/status/{payment_id} returns completed for Premium", False, error=e)
        else:
            results.add_result(
                "/api/fedapay/status/{payment_id} returns completed for Premium",
                False,
                "Skipped: No Premium payment ID available"
            )
        
        # ========================================
        # TEST 10: Check notifications for payment confirmations
        # ========================================
        try:
            response = await client.get(
                f"{API_BASE}/notifications",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                notifications = data.get("notifications", [])
                
                # Look for payment confirmation notifications
                payment_notifications = [
                    n for n in notifications
                    if n.get("type") in ["payment_confirmed", "payment_success", "subscription_activated"]
                    or "payment" in n.get("title", "").lower()
                    or "payment" in n.get("message", "").lower()
                ]
                
                has_payment_notifications = len(payment_notifications) > 0
                
                results.add_result(
                    "/api/notifications includes payment confirmation notifications",
                    has_payment_notifications,
                    f"Found {len(payment_notifications)} payment-related notifications out of {len(notifications)} total"
                )
            else:
                results.add_result(
                    "/api/notifications includes payment confirmation notifications",
                    False,
                    f"Status: {response.status_code}",
                    response.text
                )
        except Exception as e:
            results.add_result("/api/notifications includes payment confirmation notifications", False, error=e)
    
    return results

async def main():
    print("="*80)
    print("FedaPay Production-Readiness Flow Verification")
    print(f"Test URL: {BASE_URL}")
    print(f"Test Email: {TEST_EMAIL}")
    print("="*80)
    print()
    
    results = await test_production_readiness_flow()
    
    print()
    all_passed = results.summary()
    
    # Save results to file
    report_file = "/app/fedapay_production_readiness_test_report.json"
    with open(report_file, "w") as f:
        json.dump({
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "base_url": BASE_URL,
                "test_email": TEST_EMAIL,
                "all_passed": all_passed
            },
            "results": results.results,
            "test_data": {
                "user_id": results.user_id,
                "basic_payment_id": results.basic_payment_id,
                "premium_payment_id": results.premium_payment_id,
                "basic_tx_id": results.basic_tx_id,
                "premium_tx_id": results.premium_tx_id
            }
        }, f, indent=2)
    
    print(f"\nTest report saved to: {report_file}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
