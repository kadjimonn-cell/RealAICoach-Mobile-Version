#!/usr/bin/env python3
"""
Google IAP Production Readiness - Detailed Backend Verification
"""

import requests
import json
from datetime import datetime, timezone

BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"
TEST_EMAIL = "googleiap.prod.final.6dfbe881@gmail.com"
TEST_PASSWORD = "GoogleIAP#2026Aa!"

def login():
    """Login and get session"""
    session = requests.Session()
    response = session.post(f"{API_BASE}/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response.status_code == 200:
        print(f"✅ Login successful")
        return session
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def main():
    print(f"\n{'='*80}")
    print("Google IAP Production Readiness - Detailed Verification")
    print(f"{'='*80}\n")
    
    session = login()
    if not session:
        return
    
    # Get payment history
    print(f"\n{'='*80}")
    print("Payment History Details")
    print(f"{'='*80}\n")
    
    response = session.get(f"{API_BASE}/payments/history")
    if response.status_code == 200:
        data = response.json()
        payments = data.get("payments", [])
        
        print(f"Total payments: {len(payments)}\n")
        
        for idx, payment in enumerate(payments, 1):
            print(f"{'─'*80}")
            print(f"Payment #{idx}")
            print(f"{'─'*80}")
            print(json.dumps(payment, indent=2))
            print()
    
    # Get notifications
    print(f"\n{'='*80}")
    print("Notifications Details")
    print(f"{'='*80}\n")
    
    response = session.get(f"{API_BASE}/notifications")
    if response.status_code == 200:
        data = response.json()
        notifications = data.get("notifications", [])
        
        print(f"Total notifications: {len(notifications)}\n")
        
        for idx, notif in enumerate(notifications, 1):
            if "Google Play" in notif.get("message", ""):
                print(f"{'─'*80}")
                print(f"Google IAP Notification #{idx}")
                print(f"{'─'*80}")
                print(json.dumps(notif, indent=2))
                print()
    
    # Test PDF endpoints with payment IDs
    print(f"\n{'='*80}")
    print("Testing PDF Endpoints")
    print(f"{'='*80}\n")
    
    response = session.get(f"{API_BASE}/payments/history")
    if response.status_code == 200:
        data = response.json()
        payments = data.get("payments", [])
        
        for payment in payments:
            payment_id = payment.get("payment_id", "")
            if payment_id:
                pdf_url = f"{API_BASE}/payments/receipt/{payment_id}/pdf"
                print(f"Testing: {pdf_url}")
                
                pdf_response = session.get(pdf_url, allow_redirects=True)
                print(f"  Status: {pdf_response.status_code}")
                print(f"  Content-Type: {pdf_response.headers.get('Content-Type', 'N/A')}")
                print(f"  Content-Length: {len(pdf_response.content)} bytes")
                
                if pdf_response.status_code == 200:
                    if pdf_response.content[:4] == b'%PDF':
                        print(f"  ✅ Valid PDF")
                    else:
                        print(f"  ⚠️  Not a PDF (first 20 bytes: {pdf_response.content[:20]})")
                else:
                    print(f"  ❌ Failed")
                print()

if __name__ == "__main__":
    main()
