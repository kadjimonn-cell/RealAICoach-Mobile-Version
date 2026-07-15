"""
Check what the payment history API actually returns
"""
import asyncio
import httpx
import json

BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"
TEST_USER_EMAIL = "paypal.prod.retest.fix.611e6d3d@gmail.com"
TEST_USER_PASSWORD = "PayPalLive#2026Aa!"

async def check_payment_history():
    client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
    
    # Login
    print("Logging in...")
    response = await client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    )
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        return
    
    data = response.json()
    token = data.get("token") or response.cookies.get("session_token")
    
    print(f"✅ Logged in successfully")
    
    # Get payment history
    print("\nFetching payment history...")
    response = await client.get(
        f"{BASE_URL}/api/payments/history",
        headers={
            "Authorization": f"Bearer {token}",
            "Cookie": f"session_token={token}"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        payments = data.get("payments", [])
        
        print(f"\n✅ Found {len(payments)} payments")
        
        # Look for our PayPal orders
        for payment in payments:
            payment_id = payment.get("payment_id", "")
            session_id = payment.get("session_id", "")
            
            if "1UW49833CW014203Y" in [payment_id, session_id] or "7WR35562CP5880350" in [payment_id, session_id]:
                print(f"\n{'='*80}")
                print(f"Payment ID: {payment_id}")
                print(f"Session ID: {session_id}")
                print(f"Status: {payment.get('status')}")
                print(f"Plan: {payment.get('plan_id')}")
                print(f"Amount: ${payment.get('amount')}")
                print(f"Provider: {payment.get('provider')}")
                print(f"Method: {payment.get('payment_method')}")
                print(f"Created: {payment.get('created_at')}")
                print(f"\nReceipt Delivery Flags:")
                print(f"  user_receipt_sent: {payment.get('user_receipt_sent', False)}")
                print(f"  admin_receipt_sent: {payment.get('admin_receipt_sent', False)}")
                print(f"  receipt_delivery_ok: {payment.get('receipt_delivery_ok', False)}")
                print(f"  notification_sent: {payment.get('notification_sent', False)}")
                print(f"\nFull payment record:")
                print(json.dumps(payment, indent=2, default=str))
    else:
        print(f"❌ Failed to fetch payment history: {response.status_code}")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(check_payment_history())
