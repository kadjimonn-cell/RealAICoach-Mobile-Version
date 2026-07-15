"""Feature 31 Detailed Response Inspection
Inspect the actual response structure to find policy/limit fields.
"""

import requests
import json

BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"

CREDENTIALS = {
    "free": {"email": "p1.free.1779113329@example.com", "password": "P1Free#2026!Aa"},
    "basic": {"email": "f21.basic.1781338672@example.com", "password": "F21Basic#2026Aa"},
    "admin": {"email": "admin@realaicoach.app", "password": "NewAdminPass2026!"}
}


def create_session(role: str):
    """Create authenticated session."""
    creds = CREDENTIALS[role]
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    })
    
    resp = session.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=10)
    if resp.status_code == 200:
        print(f"✅ Login successful for {role}")
        return session
    else:
        print(f"❌ Login failed for {role}")
        return None


def inspect_endpoint(session, role, endpoint):
    """Inspect endpoint response structure."""
    url = f"{BASE_URL}{endpoint}"
    resp = session.get(url, timeout=10)
    
    print(f"\n{'='*100}")
    print(f"Endpoint: {endpoint}")
    print(f"Role: {role}")
    print(f"Status: {resp.status_code}")
    print(f"{'='*100}")
    
    if resp.status_code == 200:
        try:
            data = resp.json()
            print(json.dumps(data, indent=2))
        except:
            print(f"Response text: {resp.text[:500]}")
    else:
        print(f"Error response: {resp.text[:500]}")


def main():
    """Main inspection."""
    print("="*100)
    print("FEATURE 31 DETAILED RESPONSE INSPECTION")
    print("="*100)
    
    # Create sessions
    sessions = {}
    for role in ["free", "basic", "admin"]:
        sessions[role] = create_session(role)
    
    # Inspect context-sources endpoints
    endpoints = [
        "/api/ai-solver/context-sources",
        "/api/ai-problem-solver/context-sources",
        "/api/ai-solver/bootstrap",
        "/api/ai-problem-solver/bootstrap"
    ]
    
    for endpoint in endpoints:
        for role in ["free", "basic", "admin"]:
            if sessions[role]:
                inspect_endpoint(sessions[role], role, endpoint)


if __name__ == "__main__":
    main()
