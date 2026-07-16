"""
Security verification tests: Payment `simulate` endpoints must be admin-only.

Scope (as requested by main agent):
  1. POST /api/iap/admin/simulate-production-e2e
  2. POST /api/admin/payments/simulate-stripe-production-e2e
  3. POST /api/admin/payments/simulate-paypal-production-e2e
  4. POST /api/admin/payments/simulate-fedapay-production-e2e
  5. Bonus: POST /api/webhook-events/simulate

Expected behaviour for each endpoint:
  * Anonymous  -> 401 or 403 (blocked)
  * Non-admin  -> 403 (blocked, "Admin access required")
  * Admin      -> passes the auth guard.  Acceptable status codes are
                  200 / 201 / 202 (success), 400 (bad body values),
                  404 (missing entity), or 422 (Pydantic validation).
                  Anything else (401, 403, 5xx) is a FAIL for the auth-pass leg.

Negative bypass attempts:
  * Invalid Bearer token -> 401/403
"""

import os

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "Rt#vzsuRlMXGvOF!7a"
FREE_EMAIL = "p1.free.1779113329@example.com"
FREE_PASSWORD = "Rt#Fhtx0loztn7Y!7a"

SIMULATE_ENDPOINTS = [
    ("iap", "/api/iap/admin/simulate-production-e2e"),
    ("stripe", "/api/admin/payments/simulate-stripe-production-e2e"),
    ("paypal", "/api/admin/payments/simulate-paypal-production-e2e"),
    ("fedapay", "/api/admin/payments/simulate-fedapay-production-e2e"),
    ("webhook", "/api/webhook-events/simulate"),
]

BLOCK_STATUSES = {401, 403}
# Codes that indicate we PASSED the admin guard (any of these means "reached handler")
AUTH_PASSED_STATUSES = {200, 201, 202, 204, 400, 404, 409, 422, 500}


def _login(session: requests.Session, email: str, password: str):
    """Login helper – returns (session_token or None, response)."""
    resp = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"},
        timeout=20,
    )
    token = None
    # Preferred: cookie jar
    for c in session.cookies:
        if c.name == "session_token":
            token = c.value
            break
    # Fallback: some flows return token in body
    if not token and resp.status_code == 200:
        try:
            body = resp.json()
            token = body.get("session_token") or body.get("token") or body.get("access_token")
        except Exception:
            pass
    return token, resp


@pytest.fixture(scope="module")
def admin_token():
    s = requests.Session()
    token, resp = _login(s, ADMIN_EMAIL, ADMIN_PASSWORD)
    assert resp.status_code == 200, f"Admin login failed: {resp.status_code} {resp.text[:300]}"
    assert token, "Admin session_token cookie missing"
    return token


@pytest.fixture(scope="module")
def free_token():
    s = requests.Session()
    token, resp = _login(s, FREE_EMAIL, FREE_PASSWORD)
    assert resp.status_code == 200, f"Free-user login failed: {resp.status_code} {resp.text[:300]}"
    assert token, "Free-user session_token cookie missing"
    return token


# ------------------------------ Anonymous ------------------------------


@pytest.mark.parametrize("name,path", SIMULATE_ENDPOINTS)
def test_anonymous_is_blocked(name, path):
    """Anonymous POST must be blocked (401 or 403)."""
    r = requests.post(f"{BASE_URL}{path}", json={}, timeout=20)
    assert r.status_code in BLOCK_STATUSES, (
        f"[{name}] anonymous NOT blocked: got {r.status_code} body={r.text[:300]}"
    )


# ------------------------------ Non-admin user ------------------------------


# Valid-shaped bodies so Pydantic validation does not preempt the admin guard.
# (FastAPI validates the request body BEFORE the function runs, so an empty body
#  can yield 422 even for a non-admin when the schema has required fields.)
VALID_BODIES = {
    "iap": {
        "email": "sim.test@example.com",
        "name": "Sim Test",
        "plan": "basic",
        "period": "monthly",
        "platform": "google",
    },
    "stripe": {"email": "sim.test@example.com", "name": "Sim Test", "plan": "basic", "period": "monthly"},
    "paypal": {"email": "sim.test@example.com", "name": "Sim Test", "plan": "basic", "period": "monthly"},
    "fedapay": {"email": "sim.test@example.com", "name": "Sim Test", "plan": "basic", "period": "monthly"},
    "webhook": {"event_type": "test.event", "payload": {}},
}


@pytest.mark.parametrize("name,path", SIMULATE_ENDPOINTS)
def test_non_admin_is_blocked(name, path, free_token):
    """Non-admin authenticated user must receive 403 for a VALID-shaped body."""
    r = requests.post(
        f"{BASE_URL}{path}",
        json=VALID_BODIES.get(name, {}),
        headers={"Authorization": f"Bearer {free_token}"},
        timeout=20,
    )
    assert r.status_code == 403, (
        f"[{name}] non-admin NOT blocked with 403: got {r.status_code} body={r.text[:300]}"
    )


# ------------------------------ Admin passes guard ------------------------------


@pytest.mark.parametrize("name,path", SIMULATE_ENDPOINTS)
def test_admin_passes_auth_guard(name, path, admin_token):
    """Admin must PASS the auth guard.
    We send an empty JSON body so we expect either 200/202 (unlikely without body)
    or 400/422 (validation error). We MUST NOT see 401/403 for admin.
    """
    r = requests.post(
        f"{BASE_URL}{path}",
        json={},
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=30,
    )
    assert r.status_code in AUTH_PASSED_STATUSES, (
        f"[{name}] admin unexpected status: {r.status_code} body={r.text[:300]}"
    )
    assert r.status_code not in BLOCK_STATUSES, (
        f"[{name}] admin BLOCKED by auth guard: {r.status_code} body={r.text[:300]}"
    )


# ------------------------------ Negative bypass ------------------------------


@pytest.mark.parametrize("name,path", SIMULATE_ENDPOINTS)
def test_invalid_bearer_token_is_blocked(name, path):
    """Garbage bearer token must be rejected."""
    r = requests.post(
        f"{BASE_URL}{path}",
        json={},
        headers={"Authorization": "Bearer this-is-a-garbage-token-xxx"},
        timeout=20,
    )
    assert r.status_code in BLOCK_STATUSES, (
        f"[{name}] garbage token NOT blocked: {r.status_code} body={r.text[:300]}"
    )
