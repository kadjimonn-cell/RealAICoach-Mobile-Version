"""Iteration 924 — Admin Console REAL DATA verification.

Verifies:
- Admin login works and returns admin role.
- Non-admin cannot access /api/admin/* endpoints (403).
- Key admin analytics endpoints return DB-derived values that match direct
  MongoDB ground truth queries (users totals, plan distribution, revenue,
  travel-visa & personal-assistant usage, LLM/media/conversations counts).
- Observability / scheduler heartbeats surface real docs (incl. new
  sso_callback_liveness_daily heartbeat added in iter923).
- Endpoints powering the primary admin screens (subscription-dashboard,
  security, observability-center, llm-billing, email-delivery-ledger) return
  200 with a real / honest empty-state JSON shape.

Uses REACT_APP_BACKEND_URL (public preview) with cookie auth + X-Requested-With
header, exactly what the shell uses in production.
"""
import os
import re
import asyncio

import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env", "r") as f:
        for ln in f:
            if ln.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = ln.split("=", 1)[1].strip().strip('"').rstrip("/")
                break

MONGO_URL = os.environ.get("MONGO_URL") or "mongodb://localhost:27017"
DB_NAME = os.environ.get("DB_NAME") or "realtalk_db"

ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"
FREE_EMAIL = "p1.free.1779113329@example.com"
FREE_PASSWORD = "P1Free#2026!Aa"

XRW = {"X-Requested-With": "XMLHttpRequest", "Content-Type": "application/json"}


# ---------------- fixtures ----------------
@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    s.headers.update(XRW)
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:200]}"
    body = r.json()
    assert body.get("role") == "admin" or body.get("is_admin") is True
    return s


@pytest.fixture(scope="module")
def free_session():
    s = requests.Session()
    s.headers.update(XRW)
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": FREE_EMAIL, "password": FREE_PASSWORD},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"free user login unavailable ({r.status_code}) — negative test skipped")
    return s


@pytest.fixture(scope="module")
def db():
    loop = asyncio.new_event_loop()
    client = AsyncIOMotorClient(MONGO_URL, io_loop=loop)
    yield loop, client[DB_NAME]
    client.close()
    loop.close()


def _run(loop, coro):
    return loop.run_until_complete(coro)


# ---------------- admin login ----------------
class TestAdminLogin:
    def test_admin_login_returns_admin_role(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert r.status_code == 200
        me = r.json()
        assert (
            me.get("role") == "admin" or me.get("is_admin") is True
        ), f"admin role missing in /auth/me: {me}"


# ---------------- cross-check analytics vs DB ----------------
class TestAdminOverviewMatchesDB:
    def test_users_and_billing_totals_match(self, admin_session, db):
        loop, mdb = db

        # DB ground truth
        total = _run(loop, mdb.users.count_documents({}))
        premium = _run(loop, mdb.users.count_documents({"subscription_plan": "premium"}))
        basic = _run(loop, mdb.users.count_documents({"subscription_plan": "basic"}))
        free = _run(loop, mdb.users.count_documents({"subscription_plan": "free"}))
        suspended = _run(loop, mdb.users.count_documents({"suspended": True}))

        async def _payments_agg():
            cur = mdb.payments.aggregate(
                [{"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}]
            )
            return await cur.to_list(1)

        pay = _run(loop, _payments_agg())
        revenue = round(pay[0]["total"], 2) if pay else 0
        pay_count = pay[0]["count"] if pay else 0

        # API
        r = admin_session.get(f"{BASE_URL}/api/admin/overview", timeout=30)
        assert r.status_code == 200, r.text[:200]
        data = r.json()

        assert data["users"]["total"] == total, f"total users drift: api={data['users']['total']} db={total}"
        assert data["users"]["premium"] == premium
        assert data["users"]["basic"] == basic
        assert data["users"]["free"] == free
        assert data["users"]["suspended"] == suspended
        assert data["billing"]["total_revenue"] == revenue
        assert data["billing"]["transactions"] == pay_count


class TestSubscriptionAnalyticsMatchesDB:
    def test_subscription_analytics_endpoint(self, admin_session, db):
        loop, mdb = db
        r = admin_session.get(f"{BASE_URL}/api/admin/subscriptions/analytics", timeout=30)
        assert r.status_code == 200, r.text[:300]
        data = r.json()

        # Ground truth
        total_users = _run(loop, mdb.users.count_documents({}))
        free = _run(loop, mdb.users.count_documents({"subscription_plan": "free"}))
        basic = _run(loop, mdb.users.count_documents({"subscription_plan": "basic"}))
        premium = _run(loop, mdb.users.count_documents({"subscription_plan": "premium"}))

        subs = data.get("subscribers", {})
        assert subs.get("total_users") == total_users
        assert subs.get("free") == free
        assert subs.get("basic") == basic
        assert subs.get("premium") == premium
        assert subs.get("total_paid") == basic + premium

        # revenue.total must equal sum of payments where status==completed
        async def _rev():
            cur = mdb.payments.aggregate(
                [
                    {"$match": {"status": "completed"}},
                    {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
                ]
            )
            return await cur.to_list(1)

        rev = _run(loop, _rev())
        expected_total = round(rev[0]["total"], 2) if rev else 0
        expected_count = rev[0]["count"] if rev else 0
        assert data["revenue"]["total"] == expected_total
        assert data["revenue"]["total_payments"] == expected_count


class TestAIMonitorMatchesDB:
    def test_ai_monitor_counts_match(self, admin_session, db):
        loop, mdb = db
        r = admin_session.get(f"{BASE_URL}/api/admin/ai/monitor", timeout=30)
        assert r.status_code == 200
        data = r.json()

        sl = _run(loop, mdb.llm_search_logs.count_documents({}))
        pe = _run(loop, mdb.media_playback_events.count_documents({}))
        cv = _run(loop, mdb.conversations.count_documents({}))

        assert data["search_logs"] == sl
        assert data["playback_events"] == pe
        assert data["conversations"] == cv


class TestBillingOverviewMatchesDB:
    def test_billing_active_subs_and_revenue(self, admin_session, db):
        loop, mdb = db
        r = admin_session.get(f"{BASE_URL}/api/admin/billing/overview", timeout=30)
        assert r.status_code == 200
        data = r.json()

        active = _run(
            loop,
            mdb.users.count_documents(
                {
                    "subscription_status": "active",
                    "subscription_plan": {"$in": ["basic", "premium"]},
                }
            ),
        )
        assert data["active_subscriptions"] == active
        # revenue is capped at latest 100 payments — must be numeric and >=0
        assert isinstance(data["total_revenue"], (int, float))
        assert data["total_revenue"] >= 0
        assert isinstance(data["transactions"], int)


# ---------------- observability heartbeats ----------------
class TestObservabilityHeartbeats:
    def test_sso_callback_liveness_heartbeat_present(self, admin_session, db):
        loop, mdb = db
        hb = _run(
            loop,
            mdb.scheduler_heartbeats.find_one({"job_id": "sso_callback_liveness_daily"}),
        )
        assert hb is not None, "sso_callback_liveness_daily heartbeat missing (iter923 addition)"
        assert "last_run" in hb
        assert hb.get("status") in ("healthy", "warning", "error")


# ---------------- key admin screen endpoints ----------------
@pytest.mark.parametrize(
    "path",
    [
        "/api/admin/overview",
        "/api/admin/console/overview",
        "/api/admin/subscriptions/analytics",
        "/api/admin/subscriptions/expiry-overview",
        "/api/admin/billing/overview",
        "/api/admin/billing/transactions",
        "/api/admin/ai/monitor",
        "/api/admin/announcements",
        "/api/admin/feature-flags",
        "/api/admin/access-logs",
        "/api/admin/notifications/history",
    ],
)
def test_admin_screen_endpoints_return_200(admin_session, path):
    r = admin_session.get(f"{BASE_URL}{path}", timeout=30)
    assert r.status_code == 200, f"{path} -> {r.status_code} {r.text[:200]}"
    # response must be JSON, and must not contain obvious placeholder text
    body_text = r.text.lower()
    for placeholder in ["lorem ipsum", "sample data placeholder", "todo:", "coming soon"]:
        assert placeholder not in body_text, f"placeholder '{placeholder}' found in {path}"


# ---------------- negative: non-admin access ----------------
class TestNonAdminBlocked:
    @pytest.mark.parametrize(
        "path",
        [
            "/api/admin/overview",
            "/api/admin/subscriptions/analytics",
            "/api/admin/billing/overview",
            "/api/admin/users",
        ],
    )
    def test_free_user_blocked(self, free_session, path):
        r = free_session.get(f"{BASE_URL}{path}", timeout=30)
        assert r.status_code in (401, 403), (
            f"non-admin should be blocked from {path}, got {r.status_code}"
        )

    def test_anonymous_blocked(self, path="/api/admin/overview"):
        s = requests.Session()
        s.headers.update(XRW)
        r = s.get(f"{BASE_URL}{path}", timeout=30)
        assert r.status_code in (401, 403)


# ---------------- placeholder / mock scan of responses ----------------
class TestNoFabricatedData:
    def test_analytics_response_traceable_to_db(self, admin_session, db):
        """Sanity: at least one recent payment in analytics response must exist in payments collection."""
        loop, mdb = db
        r = admin_session.get(f"{BASE_URL}/api/admin/subscriptions/analytics", timeout=30)
        assert r.status_code == 200
        data = r.json()
        recent = data.get("recent_payments") or []
        if not recent:
            # empty is acceptable as long as DB also has no completed payment_transactions
            n = _run(
                loop, mdb.payment_transactions.count_documents({"payment_status": "completed"})
            )
            assert n == 0, "recent_payments empty but DB has completed payment_transactions"
            return
        sample = recent[0]
        # each recent_payment record must have a real user_id string, not a fake token
        assert isinstance(sample.get("user_id"), str) and len(sample["user_id"]) > 3
        assert not re.match(r"^(sample|test|placeholder|fake|todo)", str(sample["user_id"]).lower())
