"""
Iteration 923 — Backend tests for the daily SSO callback liveness scheduler job.

Covers:
  * Happy-path run of ``scheduled_sso_callback_liveness_probe`` on the live
    preview domain (healthy, both providers registry_aligned, doc + heartbeat
    persisted).
  * Live reachability of derived callback URLs via HTTPS (curl-equivalent).
  * Mismatch + additive auto-fix: mutate ``MS_SSO_REGISTERED_REDIRECT_URIS``
    to omit the active base, run the job, then verify:
      - report contains 1 mismatch + 1 autofix
      - os.environ MS_SSO_REGISTERED_REDIRECT_URIS now includes the active base
        (original entries preserved — additive only)
      - backend/.env line was persisted with both entries
      - realtime alert with alert_type='sso_callback_liveness' recorded in
        admin_push_notifications collection
      - ORIGINAL value is restored to os.environ AND backend/.env in a finally
        block so backend stays valid.
  * Scheduler registration for ``sso_callback_liveness_daily`` in scheduler.py.
  * ``scheduled_sso_callback_liveness_probe`` importable from the
    ``scheduler_jobs`` facade.
  * Backend boot: /api/health returns 200 and no import errors are present in
    the supervisor error log for sso_auth_health.
"""
import asyncio
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests

# Ensure /app/backend on sys.path so `scheduler_jobs`, `routes.db` etc import.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load backend/.env explicitly (pytest may run without the uvicorn env loader).
from dotenv import load_dotenv  # noqa: E402
load_dotenv(BACKEND_DIR / ".env")

BASE_URL = (
    os.environ.get("PYTEST_EXTERNAL_PREVIEW_BASE")
    or os.environ.get("REACT_APP_BACKEND_URL")
    or ""
).rstrip("/")

ENV_PATH = BACKEND_DIR / ".env"
ORIGINAL_MS_ENV_LINE = "MS_SSO_REGISTERED_REDIRECT_URIS=https://visa-polish-v2.preview.emergentagent.com,https://realaicoach.app"
ORIGINAL_MS_VALUE = "https://visa-polish-v2.preview.emergentagent.com,https://realaicoach.app"


# ---------------------------------------------------------------------------
# Regression sanity
# ---------------------------------------------------------------------------
class TestBackendSanity:
    def test_health_endpoint_200(self):
        assert BASE_URL, "REACT_APP_BACKEND_URL not configured"
        r = requests.get(f"{BASE_URL}/api/health", timeout=15)
        assert r.status_code == 200, r.text[:300]

    def test_derived_callback_urls_reachable(self):
        """Derived callbacks respond with non-404/<500 on the live domain."""
        assert BASE_URL
        ms = requests.get(f"{BASE_URL}/api/auth/microsoft/callback", timeout=15, allow_redirects=False)
        ap = requests.get(f"{BASE_URL}/api/auth/apple/callback", timeout=15, allow_redirects=False)
        assert ms.status_code != 404 and ms.status_code < 500, f"MS={ms.status_code}"
        assert ap.status_code != 404 and ap.status_code < 500, f"Apple={ap.status_code}"


# ---------------------------------------------------------------------------
# Import surface / scheduler registration
# ---------------------------------------------------------------------------
class TestImportAndSchedulerRegistration:
    def test_facade_exposes_probe(self):
        from scheduler_jobs import scheduled_sso_callback_liveness_probe  # noqa: F401
        assert callable(scheduled_sso_callback_liveness_probe)

    def test_scheduler_registers_daily_job(self):
        sched_src = (BACKEND_DIR / "scheduler.py").read_text(encoding="utf-8")
        # Must register with the exact id + CronTrigger(hour=6, minute=20)
        assert 'id="sso_callback_liveness_daily"' in sched_src
        # Find the block around the id and verify CronTrigger schedule
        m = re.search(
            r"CronTrigger\(hour=6,\s*minute=20\)\s*,\s*id=\"sso_callback_liveness_daily\"",
            sched_src,
        )
        assert m, "CronTrigger(hour=6, minute=20) not found for sso_callback_liveness_daily"

    def test_no_import_errors_in_backend_log(self):
        """No sso_auth_health traceback/ImportError in the current supervisor err log."""
        log = Path("/var/log/supervisor/backend.err.log")
        if not log.exists():
            pytest.skip("backend.err.log not present")
        # Read tail (last ~200KB) — full file can be large.
        with log.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 200_000))
            tail = f.read().decode("utf-8", errors="replace")
        offenders = [
            line for line in tail.splitlines()
            if ("sso_auth_health" in line or "sso_callback_liveness" in line)
            and ("Traceback" in line or "ImportError" in line or '"level": "ERROR"' in line)
        ]
        assert not offenders, f"Found errors: {offenders[:5]}"


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------
class TestHappyPathProbe:
    def test_probe_runs_healthy_and_persists(self):
        from scheduler_jobs import scheduled_sso_callback_liveness_probe
        from routes.db import db

        result = asyncio.get_event_loop().run_until_complete(
            scheduled_sso_callback_liveness_probe()
        )
        assert result.get("status") == "ok", result
        assert result.get("healthy") is True, result
        assert result.get("failures") == []
        assert result.get("mismatches") == []

        # Verify persisted report doc
        doc = asyncio.get_event_loop().run_until_complete(
            db.sso_callback_liveness_reports.find_one({"report_id": "latest"}, {"_id": 0})
        )
        assert doc is not None
        assert doc["healthy"] is True
        assert doc["active_base"].startswith("https://")
        assert "checked_at" in doc
        # both providers present, reachable, registry_aligned
        for prov in ("microsoft", "apple"):
            p = doc["providers"][prov]
            assert p["reachable"] is True, f"{prov} unreachable: {p}"
            assert p["http_status"] is not None
            assert p["http_status"] != 404 and p["http_status"] < 500
            assert p["registry_aligned"] is True, f"{prov} not aligned: {p}"
            assert p["callback_url"].endswith(f"/api/auth/{prov}/callback")

        # Verify heartbeat persisted
        hb = asyncio.get_event_loop().run_until_complete(
            db.scheduler_heartbeats.find_one({"job_id": "sso_callback_liveness_daily"}, {"_id": 0})
        )
        assert hb is not None
        assert hb["status"] == "healthy"
        assert "last_run" in hb


# ---------------------------------------------------------------------------
# Mismatch + additive auto-fix + realtime alert
# ---------------------------------------------------------------------------
class TestMismatchAutofixAndAlert:
    def test_autofix_appends_active_base_and_emits_alert(self):
        from scheduler_jobs import scheduled_sso_callback_liveness_probe
        from routes.db import db
        # Local import — module has a cooldown dict we must reset so this run
        # actually persists the alert.
        from routes import admin_push_notifications as apn

        active_base = (
            os.environ.get("SSO_REDIRECT_BASE_URL")
            or os.environ.get("FRONTEND_BASE_URL")
            or ""
        ).rstrip("/")
        assert active_base, "SSO_REDIRECT_BASE_URL / FRONTEND_BASE_URL not configured"

        original_env_text = ENV_PATH.read_text(encoding="utf-8")
        original_os_value = os.environ.get("MS_SSO_REGISTERED_REDIRECT_URIS", "")

        # Mutate: drop active base, keep only realaicoach.app
        mutated_value = "https://realaicoach.app"
        os.environ["MS_SSO_REGISTERED_REDIRECT_URIS"] = mutated_value

        # Reset alert cooldown so emit_realtime_alert actually pushes now.
        try:
            apn._last_pushed.pop("sso_callback_liveness", None)
        except Exception:
            pass

        # Baseline: capture existing recent alert count so we can detect a NEW
        # alert vs old ones.
        pre_count = asyncio.get_event_loop().run_until_complete(
            db.admin_push_notifications.count_documents({"type": "sso_callback_liveness"})
        )

        try:
            result = asyncio.get_event_loop().run_until_complete(
                scheduled_sso_callback_liveness_probe()
            )
            assert result.get("status") == "ok", result

            # (a) Result summary: 1 mismatch + 1 autofix
            assert len(result.get("mismatches", [])) == 1, result
            assert len(result.get("autofixes", [])) == 1, result
            assert result.get("healthy") is False

            # (b) os.environ list now contains active base AND original entry
            #     (additive — original preserved).
            current = os.environ.get("MS_SSO_REGISTERED_REDIRECT_URIS", "")
            parts = [p.strip() for p in current.split(",") if p.strip()]
            assert active_base in parts, f"active_base missing from env: {parts}"
            assert "https://realaicoach.app" in parts, (
                f"original entry not preserved (additive-only violation): {parts}"
            )

            # (c) backend/.env line updated to include both
            env_text = ENV_PATH.read_text(encoding="utf-8")
            env_line = None
            for line in env_text.splitlines():
                if line.startswith("MS_SSO_REGISTERED_REDIRECT_URIS="):
                    env_line = line
                    break
            assert env_line, "MS_SSO_REGISTERED_REDIRECT_URIS not found in .env"
            assert active_base in env_line
            assert "https://realaicoach.app" in env_line

            # (d) report doc mismatches/autofixes populated
            doc = asyncio.get_event_loop().run_until_complete(
                db.sso_callback_liveness_reports.find_one({"report_id": "latest"}, {"_id": 0})
            )
            assert doc is not None
            assert len(doc.get("mismatches", [])) == 1
            assert len(doc.get("autofixes", [])) == 1
            ms_probe = doc["providers"]["microsoft"]
            assert ms_probe["autofix_applied"] is True
            # NOTE: registered_bases in the persisted report is a snapshot of the
            # PRE-autofix env (by design — records the drift that was detected).
            assert ms_probe["registry_aligned"] is False
            assert "https://realaicoach.app" in ms_probe["registered_bases"]
            assert active_base not in ms_probe["registered_bases"]

            # (e) alert recorded (admin_push_notifications collection)
            post_count = asyncio.get_event_loop().run_until_complete(
                db.admin_push_notifications.count_documents({"type": "sso_callback_liveness"})
            )
            assert post_count > pre_count, (
                f"No new sso_callback_liveness alert recorded (pre={pre_count} post={post_count})"
            )

            latest_alert = asyncio.get_event_loop().run_until_complete(
                db.admin_push_notifications.find_one(
                    {"type": "sso_callback_liveness"},
                    sort=[("timestamp", -1)],
                    projection={"_id": 0},
                )
            )
            assert latest_alert is not None
            assert latest_alert["type"] == "sso_callback_liveness"
            assert latest_alert["severity"] in ("info", "warning")
        finally:
            # CRITICAL restore — never leave the backend with a broken env.
            os.environ["MS_SSO_REGISTERED_REDIRECT_URIS"] = ORIGINAL_MS_VALUE
            env_text = ENV_PATH.read_text(encoding="utf-8")
            restored = re.sub(
                r"^MS_SSO_REGISTERED_REDIRECT_URIS=.*$",
                ORIGINAL_MS_ENV_LINE,
                env_text,
                flags=re.M,
            )
            if "MS_SSO_REGISTERED_REDIRECT_URIS=" not in restored:
                restored = original_env_text  # fallback — restore from snapshot
            ENV_PATH.write_text(restored, encoding="utf-8")

            # sanity: assert restore succeeded
            after = ENV_PATH.read_text(encoding="utf-8")
            assert ORIGINAL_MS_ENV_LINE in after, "FAILED TO RESTORE .env — manual fix required"
            assert os.environ["MS_SSO_REGISTERED_REDIRECT_URIS"] == ORIGINAL_MS_VALUE
