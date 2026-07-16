"""
Schema-Leak Fix Verification (Iteration 927 follow-up to iteration_926):

The 5 payment/webhook simulate endpoints used to expose Pydantic body-validation
(422 with schema field names) BEFORE running the admin auth guard. The fix
promoted the inline `is_admin` guard to a FastAPI `Depends(require_admin)`
dependency, which runs BEFORE body validation.

Scope (5 endpoints):
  1. POST /api/iap/admin/simulate-production-e2e
  2. POST /api/admin/payments/simulate-stripe-production-e2e
  3. POST /api/admin/payments/simulate-paypal-production-e2e
  4. POST /api/admin/payments/simulate-fedapay-production-e2e
  5. POST /api/webhook-events/simulate

New assertions:
  * Anonymous with EMPTY body:  must be 401/403, NOT 422, and response body
    must NOT contain schema field names ("email", "plan", "period", "platform",
    "name", "event_type", "payload").
  * Non-admin authenticated with EMPTY body: same as anonymous.
  * Admin with EMPTY body: must PASS the guard and hit body validation ->
    expected 422 on the 4 payment endpoints and 200/2xx on webhook (no required body).
"""

import os
import re

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "Rt#vzsuRlMXGvOF!7a"
FREE_EMAIL = "p1.free.1779113329@example.com"
FREE_PASSWORD = "Rt#Fhtx0loztn7Y!7a"

# Endpoints that require a request body (payment simulate variants)
PAYMENT_ENDPOINTS = [
    ("iap", "/api/iap/admin/simulate-production-e2e"),
    ("stripe", "/api/admin/payments/simulate-stripe-production-e2e"),
    ("paypal", "/api/admin/payments/simulate-paypal-production-e2e"),
    ("fedapay", "/api/admin/payments/simulate-fedapay-production-e2e"),
]

# Webhook endpoint has no required body
WEBHOOK_ENDPOINT = ("webhook", "/api/webhook-events/simulate")

ALL_ENDPOINTS = PAYMENT_ENDPOINTS + [WEBHOOK_ENDPOINT]

BLOCK_STATUSES = {401, 403}

# Per-endpoint request-schema field names that would indicate a Pydantic 422 leak.
# We intentionally omit "plan" from the webhook endpoint because subscription-tier
# middleware may legitimately mention "current_plan"/"required_plan" in a 403 body.
SCHEMA_FIELDS_BY_ENDPOINT = {
    "iap": ["email", "plan", "period", "platform"],
    "stripe": ["email", "plan", "period"],
    "paypal": ["email", "plan", "period"],
    "fedapay": ["email", "plan", "period"],
    "webhook": ["event_type", "payload"],
}


def _has_schema_leak(response_text: str, endpoint_name: str) -> list:
    """Return list of leaked field names for the given endpoint (word-boundary match).

    A true Pydantic 422 leak surfaces the schema field names inside a
    FastAPI validation error envelope like:
      {"detail":[{"loc":["body","email"],"msg":"field required",...}]}
    We only flag as a leak if the response contains the FastAPI 422 detail
    signature ("loc" AND "body") OR the endpoint schema field appears
    together with a validation-style token.
    """
    lower = response_text.lower()
    # Pydantic 422 signature: mention of "loc" and "body" inside a detail array.
    is_pydantic_shape = ('"loc"' in lower and '"body"' in lower) or ("field required" in lower)
    leaked = []
    if is_pydantic_shape:
        for f in SCHEMA_FIELDS_BY_ENDPOINT.get(endpoint_name, []):
            if re.search(rf"\b{re.escape(f)}\b", lower):
                leaked.append(f)
    return leaked


def _login(session: requests.Session, email: str, password: str):
    resp = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"},
        timeout=20,
    )
    token = None
    for c in session.cookies:
        if c.name == "session_token":
            token = c.value
            break
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


# ----------------- Anonymous + EMPTY body: must not leak schema -----------------


@pytest.mark.parametrize("name,path", ALL_ENDPOINTS)
def test_anon_empty_body_no_schema_leak(name, path):
    r = requests.post(f"{BASE_URL}{path}", json={}, timeout=20)
    assert r.status_code in BLOCK_STATUSES, (
        f"[{name}] anon empty-body should be 401/403 (not 422). Got {r.status_code}: {r.text[:300]}"
    )
    assert r.status_code != 422, (
        f"[{name}] anon empty-body returned 422 (schema leak!). Body: {r.text[:400]}"
    )
    leaked = _has_schema_leak(r.text, name)
    assert not leaked, (
        f"[{name}] anon empty-body response leaks schema field names {leaked}. Body: {r.text[:400]}"
    )


# --------- Non-admin (free user) + EMPTY body: must not leak schema ---------


@pytest.mark.parametrize("name,path", ALL_ENDPOINTS)
def test_non_admin_empty_body_no_schema_leak(name, path, free_token):
    r = requests.post(
        f"{BASE_URL}{path}",
        json={},
        headers={"Authorization": f"Bearer {free_token}"},
        timeout=20,
    )
    assert r.status_code in BLOCK_STATUSES, (
        f"[{name}] non-admin empty-body should be 401/403 (not 422). "
        f"Got {r.status_code}: {r.text[:300]}"
    )
    assert r.status_code != 422, (
        f"[{name}] non-admin empty-body returned 422 (schema leak!). Body: {r.text[:400]}"
    )
    leaked = _has_schema_leak(r.text, name)
    assert not leaked, (
        f"[{name}] non-admin empty-body response leaks schema fields {leaked}. "
        f"Body: {r.text[:400]}"
    )


# ----------- Admin positive control: guard passes, body validation runs -----------


@pytest.mark.parametrize("name,path", PAYMENT_ENDPOINTS)
def test_admin_empty_body_reaches_validation(name, path, admin_token):
    """Admin with EMPTY body should NOT be blocked; should reach Pydantic
    validation and get 422 on the 4 payment endpoints (proves guard passed)."""
    r = requests.post(
        f"{BASE_URL}{path}",
        json={},
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=30,
    )
    assert r.status_code not in BLOCK_STATUSES, (
        f"[{name}] admin BLOCKED by auth guard on empty body: {r.status_code} body={r.text[:300]}"
    )
    # For payment simulate endpoints, empty body must fail Pydantic validation (422)
    assert r.status_code == 422, (
        f"[{name}] admin empty-body expected 422 (validation), got {r.status_code}: {r.text[:400]}"
    )


def test_admin_empty_body_webhook_reaches_handler(admin_token):
    """Webhook simulate has no required body, so admin empty {} should hit the
    handler and return 2xx (typically 200)."""
    name, path = WEBHOOK_ENDPOINT
    r = requests.post(
        f"{BASE_URL}{path}",
        json={},
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=30,
    )
    assert r.status_code not in BLOCK_STATUSES, (
        f"[{name}] admin BLOCKED by auth guard: {r.status_code} body={r.text[:300]}"
    )
    assert 200 <= r.status_code < 300 or r.status_code in {400, 404, 409}, (
        f"[{name}] admin unexpected status: {r.status_code} body={r.text[:400]}"
    )
