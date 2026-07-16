"""
Iteration 928 — Full admin-surface schema-leak sweep verification.

Verifies the 14 endpoints newly promoted to Depends(require_admin) don't
leak Pydantic schema field names in a 422 when anonymous or non-admin
sends an empty body. Also verifies:
  - The 1 intentionally skipped endpoint (id_checker_send_message) still
    accepts a non-admin authenticated user (no admin-required 403).
  - Admin positive control: empty body must NOT return 401/403 (guard passed).

METHOD:
  For each endpoint, POST/PUT `{}` as anon, as non-admin free user, and as
  admin. Anon/non-admin must be in {401, 403} (never 422). Admin must NOT
  be in {401, 403}.

Notes:
  * Cookie POSTs may be blocked by CSRF middleware → still 403 (that's a
    PASS for negative tests, so we use Authorization: Bearer <session-token>).
  * Some /api/admin/* paths may be intercepted by platform admin-path
    middleware and return 403 before reaching require_admin — still PASS.
  * Free user on some paths may hit subscription-tier 403 — that's PASS
    (schema fields are not leaked).
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

# (name, method, path)
PROMOTED_ENDPOINTS = [
    ("ai_alerts_config",      "PUT",  "/api/admin/ai-alerts/config"),
    ("ai_support_configure",  "POST", "/api/admin/ai-support/configure"),
    ("scaling_rules_create",  "POST", "/api/admin/scaling/rules"),
    ("scaling_rules_update",  "PUT",  "/api/admin/scaling/rules/test123"),
    ("scaling_trigger",       "POST", "/api/admin/scaling/trigger"),
    ("executive_risk_actions","POST", "/api/admin/executive/risk-actions"),
    ("iap_commission_policy", "PUT",  "/api/iap/admin/commission-policy"),
    ("iap_sandbox_validation","POST", "/api/iap/admin/run-live-sandbox-validation"),
    ("system_repair_config",  "POST", "/api/admin/system/repair-config"),
    ("email_override_approve","POST", "/api/email-notifications/template-policies/override-approval"),
    ("email_override_revoke", "POST", "/api/email-notifications/template-policies/override-revoke"),
    ("email_manual_override", "POST", "/api/email-notifications/overrides/manual"),
    ("jobs_admin_decide",     "POST", "/api/jobs/admin/approvals/decide"),
    ("jobs_admin_respond",    "POST", "/api/jobs/admin/support/respond"),
]

# Endpoint intentionally SKIPPED (mixed-role user↔admin messaging).
SKIPPED_ENDPOINT = ("id_checker_messages", "POST", "/api/id-checker/messages")

BLOCK_STATUSES = {401, 403}

# Schema-leak detection: only true if the response looks like a FastAPI 422
# body-validation envelope containing "loc"+"body" or "field required", AND
# it names one of the known request-schema fields for that endpoint.
SCHEMA_FIELDS = {
    "ai_alerts_config":      ["config", "email_recipients", "alert_type", "enabled", "threshold"],
    "ai_support_configure":  ["config", "enabled", "provider", "model", "prompt"],
    "scaling_rules_create":  ["service", "metric", "threshold", "scale_up_step", "scale_down_step", "cooldown_seconds"],
    "scaling_rules_update":  ["service", "metric", "threshold", "scale_up_step"],
    "scaling_trigger":       ["service", "instances", "direction", "reason"],
    "executive_risk_actions":["action", "target", "reason", "risk_id"],
    "iap_commission_policy": ["platform", "commission_pct", "policy", "effective_date"],
    "iap_sandbox_validation":["environment", "scope", "run_id"],
    "system_repair_config":  ["config", "component", "action"],
    "email_override_approve":["template_key", "approved", "approval_id"],
    "email_override_revoke": ["template_key", "revoke_reason"],
    "email_manual_override": ["template_key", "optimized_subject"],
    "jobs_admin_decide":     ["approval_id", "decision", "notes"],
    "jobs_admin_respond":    ["ticket_id", "message"],
}


def _schema_leak(response_text: str, name: str) -> list:
    lower = response_text.lower()
    is_pydantic_shape = (
        ('"loc"' in lower and '"body"' in lower) or ("field required" in lower)
    )
    leaked = []
    if is_pydantic_shape:
        for f in SCHEMA_FIELDS.get(name, []):
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
    assert token, "Admin session_token missing"
    return token


@pytest.fixture(scope="module")
def free_token():
    s = requests.Session()
    token, resp = _login(s, FREE_EMAIL, FREE_PASSWORD)
    assert resp.status_code == 200, f"Free user login failed: {resp.status_code} {resp.text[:300]}"
    assert token, "Free session_token missing"
    return token


def _do(method: str, url: str, headers=None, json_body=None, timeout=20):
    return requests.request(method, url, headers=headers or {}, json=json_body, timeout=timeout)


# ------- Anon empty body -------


@pytest.mark.parametrize("name,method,path", PROMOTED_ENDPOINTS)
def test_anon_empty_body_no_schema_leak(name, method, path):
    r = _do(method, f"{BASE_URL}{path}", json_body={})
    assert r.status_code in BLOCK_STATUSES, (
        f"[{name}] anon: expected 401/403 got {r.status_code} body={r.text[:300]}"
    )
    assert r.status_code != 422, (
        f"[{name}] anon leaked 422 body={r.text[:400]}"
    )
    leaked = _schema_leak(r.text, name)
    assert not leaked, f"[{name}] anon leaked schema fields {leaked}: {r.text[:400]}"


# ------- Non-admin free user empty body -------


# Non-admin acceptable statuses:
#   401/403 = auth guard blocked (canonical)
#   410     = route retired by legacy-jobs middleware (orthogonal, no leak)
#   404     = route family not exposed at that path (no leak)
# We reject 422 specifically because that would indicate Pydantic body
# validation ran before auth guard.
NON_ADMIN_ACCEPTABLE = {401, 403, 404, 410}


@pytest.mark.parametrize("name,method,path", PROMOTED_ENDPOINTS)
def test_non_admin_empty_body_no_schema_leak(name, method, path, free_token):
    r = _do(
        method, f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {free_token}"},
        json_body={},
    )
    assert r.status_code != 422, (
        f"[{name}] non-admin leaked 422 body={r.text[:400]}"
    )
    assert r.status_code in NON_ADMIN_ACCEPTABLE, (
        f"[{name}] non-admin unexpected {r.status_code}: {r.text[:300]}"
    )
    leaked = _schema_leak(r.text, name)
    assert not leaked, (
        f"[{name}] non-admin leaked schema fields {leaked}: {r.text[:400]}"
    )


# ------- Admin positive control: NOT blocked by auth guard -------


@pytest.mark.parametrize("name,method,path", PROMOTED_ENDPOINTS)
def test_admin_empty_body_guard_passes(name, method, path, admin_token):
    r = _do(
        method, f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json_body={},
        timeout=30,
    )
    # Guard passed means we're NOT in {401, 403}. Handler may then return
    # 422/400/404/409/200/500 depending on body-validation and app logic.
    assert r.status_code not in BLOCK_STATUSES, (
        f"[{name}] admin BLOCKED with {r.status_code}: {r.text[:400]}"
    )


# ------- REGRESSION: id_checker_send_message must allow non-admin -------


def test_id_checker_send_message_allows_non_admin(free_token):
    """The intentionally-skipped endpoint (mixed-role) must NOT reject a
    non-admin authenticated user with an 'admin required' 403."""
    name, method, path = SKIPPED_ENDPOINT
    r = _do(
        method, f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {free_token}"},
        json_body={},
    )
    # Any status EXCEPT a 403-with-admin-required is fine.
    if r.status_code == 403:
        body_lower = (r.text or "").lower()
        assert "admin" not in body_lower or "admin access required" not in body_lower, (
            f"[{name}] free user incorrectly rejected as admin-required: {r.text[:400]}"
        )
    # Otherwise 200/400/404/422 are all acceptable app-level responses.
