#!/usr/bin/env python3
"""
Feature 26 cycle runner (monitoring hold mode)

Runs:
1) Backend monitoring check
2) P1.5 read parity pack
3) Free-user admin-block + admin-allow E2E (API/cookie/browser-testid)

No destructive retirement action is executed.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import requests
from playwright.async_api import async_playwright


BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"

FREE_EMAIL = "jobs.free.final.90705154@gmail.com"
FREE_PASSWORD = "JobsFree#2026Aa!"

ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"


def run_script(command: list[str]) -> Dict[str, Any]:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        return {
            "command": command,
            "exit_code": completed.returncode,
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-2000:],
        }
    except Exception as exc:
        return {
            "command": command,
            "exit_code": 1,
            "error": str(exc),
        }


def run_script_with_retry(command: list[str], retries: int = 2, sleep_seconds: int = 4) -> Dict[str, Any]:
    attempt = 0
    last_result: Dict[str, Any] = {}
    while attempt <= retries:
        result = run_script(command)
        last_result = result
        if result.get("exit_code") == 0:
            result["attempt"] = attempt + 1
            return result

        combined = f"{result.get('stdout_tail', '')}\n{result.get('stderr_tail', '')}".lower()
        if "429" in combined or "just a moment" in combined:
            attempt += 1
            if attempt <= retries:
                time.sleep(sleep_seconds)
                continue
        result["attempt"] = attempt + 1
        return result

    last_result["attempt"] = attempt + 1
    return last_result


def login_cookie(email: str, password: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"})
    response = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )
    response.raise_for_status()
    return s


async def browser_testid_counts(base_url: str, email: str, password: str) -> Dict[str, Any]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        async def actor_probe(route: str, test_ids: list[str]) -> Dict[str, Any]:
            context = await browser.new_context(service_workers='block')
            page = await context.new_page()
            await page.goto(base_url, wait_until='domcontentloaded')
            login_result = await page.evaluate(
                """async ({email, password}) => {
                  try {
                    const r = await fetch('/api/auth/login', {
                      method: 'POST',
                      headers: {'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
                      credentials: 'include',
                      body: JSON.stringify({email, password})
                    });
                    let data = {};
                    try { data = await r.json(); } catch (e) { data = {raw: 'non-json'}; }
                    return {status: r.status, data};
                  } catch (error) {
                    return {status: 0, error: String(error)};
                  }
                }""",
                {"email": email, "password": password},
            )
            await page.goto(f"{base_url}{route}", wait_until='domcontentloaded')
            await page.wait_for_timeout(2000)
            counts = {}
            for tid in test_ids:
                counts[tid] = await page.locator(f'[data-testid="{tid}"]').count()
            final_url = page.url
            await context.close()
            return {
                "login": login_result,
                "final_url": final_url,
                "counts": counts,
            }

        free_admin = await actor_probe(
            "/job-platform-admin",
            ["job-platform-admin-route", "job-platform-admin-title", "job-platform-admin-events"],
        )
        free_candidate = await actor_probe(
            "/job-platform-candidate",
            ["job-platform-candidate-route"],
        )

        await browser.close()
        return {
            "free_admin": free_admin,
            "free_candidate": free_candidate,
        }


async def _run_admin_block_e2e_for_base(base_url: str) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        async def actor_probe(email: str, password: str, route: str, test_ids: list[str]) -> Dict[str, Any]:
            context = await browser.new_context(service_workers='block')
            page = await context.new_page()
            await page.goto(base_url, wait_until='domcontentloaded')
            login_result = await page.evaluate(
                """async ({email, password}) => {
                  try {
                    const r = await fetch('/api/auth/login', {
                      method: 'POST',
                      headers: {'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
                      credentials: 'include',
                      body: JSON.stringify({email, password})
                    });
                    let data = {};
                    try { data = await r.json(); } catch (e) { data = {raw: 'non-json'}; }
                    return {status: r.status, data};
                  } catch (error) {
                    return {status: 0, error: String(error)};
                  }
                }""",
                {"email": email, "password": password},
            )

            await page.goto(f"{base_url}{route}", wait_until='domcontentloaded')
            await page.wait_for_timeout(2000)
            counts = {}
            for tid in test_ids:
                counts[tid] = await page.locator(f'[data-testid="{tid}"]').count()
            final_url = page.url
            await context.close()
            return {
                "login": login_result,
                "final_url": final_url,
                "counts": counts,
            }

        free_admin = await actor_probe(
            FREE_EMAIL,
            FREE_PASSWORD,
            "/job-platform-admin",
            ["job-platform-admin-route", "job-platform-admin-title", "job-platform-admin-events"],
        )
        free_candidate = await actor_probe(
            FREE_EMAIL,
            FREE_PASSWORD,
            "/job-platform-candidate",
            ["job-platform-candidate-route"],
        )
        admin_admin = await actor_probe(
            ADMIN_EMAIL,
            ADMIN_PASSWORD,
            "/job-platform-admin",
            ["job-platform-admin-route", "job-platform-admin-title", "job-platform-admin-events"],
        )

        await browser.close()

    free_blocked = (
        free_admin["counts"].get("job-platform-admin-route", 0) == 0
        and free_admin["counts"].get("job-platform-admin-title", 0) == 0
    )
    free_candidate_ok = (
        free_candidate["counts"].get("job-platform-candidate-route", 0) >= 1
        or "/job-platform-candidate" in str(free_candidate.get("final_url", ""))
    )
    admin_ok = (
        admin_admin["counts"].get("job-platform-admin-route", 0) >= 1
        and admin_admin["counts"].get("job-platform-admin-title", 0) >= 1
    )

    artifact = {
        "timestamp": now.isoformat(),
        "scope": "feature26_free_user_admin_block_e2e",
        "locked_protocol": {"feature_number": 26, "feature_id": "jobs-portal"},
        "base_url": base_url,
        "accounts": {
            "free_non_otp": FREE_EMAIL,
            "admin": ADMIN_EMAIL,
        },
        "results": {
            "free_login_api_statuses": [free_admin.get("login", {}).get("status")],
            "free_admin_attempt": {
                "final_url": free_admin["final_url"],
                "admin_route_testid_count": free_admin["counts"].get("job-platform-admin-route", 0),
                "admin_title_testid_count": free_admin["counts"].get("job-platform-admin-title", 0),
                "admin_events_testid_count": free_admin["counts"].get("job-platform-admin-events", 0),
                "verdict": "blocked_from_admin_surface" if free_blocked else "unexpected_admin_surface_visible",
            },
            "free_allowed_route_check": {
                "route": "/job-platform-candidate",
                "final_url": free_candidate["final_url"],
                "candidate_route_testid_count": free_candidate["counts"].get("job-platform-candidate-route", 0),
                "verdict": "allowed_route_reachable" if free_candidate_ok else "candidate_route_not_reachable",
            },
            "admin_login_api_statuses": [admin_admin.get("login", {}).get("status")],
            "admin_route_check": {
                "route": "/job-platform-admin",
                "final_url": admin_admin["final_url"],
                "admin_route_testid_count": admin_admin["counts"].get("job-platform-admin-route", 0),
                "admin_title_testid_count": admin_admin["counts"].get("job-platform-admin-title", 0),
                "admin_events_testid_count": admin_admin["counts"].get("job-platform-admin-events", 0),
                "verdict": "admin_route_reachable" if admin_ok else "admin_route_not_reachable",
            },
            "admin_login_control_status": admin_admin.get("login", {}).get("status"),
            "notes": [
                "Cycle-runner probe uses Playwright browser route checks with data-testid validation.",
            ],
        },
        "overall_verdict": "pass" if (free_blocked and free_candidate_ok and admin_ok) else "fail",
        "notes": [
            "Validation executed on current codebase and global locked protocol context.",
            "No legacy read route pruning/deletion executed.",
        ],
    }

    ts = now.strftime("%Y%m%dT%H%M%SZ")
    out = Path(f"/app/test_reports/feature26_free_user_admin_block_e2e_{ts}.json")
    out.write_text(json.dumps(artifact, indent=2))

    return {
        "base_url": base_url,
        "artifact": str(out),
        "overall_verdict": artifact["overall_verdict"],
        "details": {
            "free_blocked": free_blocked,
            "free_candidate_ok": free_candidate_ok,
            "admin_ok": admin_ok,
        },
    }


def run_admin_block_e2e() -> Dict[str, Any]:
    base_candidates = [BASE_URL, "http://127.0.0.1:3000"]
    last_result: Dict[str, Any] = {}
    for base in base_candidates:
        try:
            result = asyncio.run(_run_admin_block_e2e_for_base(base))
            last_result = result
            if result.get("overall_verdict") == "pass":
                return result
        except Exception as exc:
            last_result = {
                "base_url": base,
                "overall_verdict": "fail",
                "error": str(exc),
            }
    return last_result


def main() -> int:
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%dT%H%M%SZ")

    monitoring = run_script_with_retry(["python", "/app/feature26_monitoring_test.py"])
    parity = run_script_with_retry(["python", "/app/feature26_read_parity_pack.py"])
    admin_block = run_admin_block_e2e()

    summary = {
        "timestamp": now.isoformat(),
        "scope": "feature26_cycle_runner",
        "locked_protocol": {"feature_number": 26, "feature_id": "jobs-portal"},
        "steps": {
            "monitoring": monitoring,
            "read_parity_pack": parity,
            "free_user_admin_block_e2e": admin_block,
        },
        "policy_guardrails": {
            "legacy_read_pruning_executed": False,
            "allowed_action": "monitoring_and_evidence_generation",
            "blocked_action": "legacy_read_prune_or_delete_without_signoff_and_sustained_governance_gates",
        },
    }

    out = Path(f"/app/test_reports/feature26_cycle_runner_{ts}.json")
    latest = Path("/app/test_reports/feature26_cycle_runner_latest.json")
    payload = json.dumps(summary, indent=2)
    out.write_text(payload)
    latest.write_text(payload)
    print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
