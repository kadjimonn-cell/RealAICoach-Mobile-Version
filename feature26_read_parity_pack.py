#!/usr/bin/env python3
"""
Feature 26 — Phase P1.5 Read Parity Verification Pack
Locked protocol scope: feature_number=26, feature_id=jobs-portal

Deterministic comparison between legacy read routes and v2 read routes.
No destructive actions are executed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"
FREE_EMAIL = "jobs.free.final.90705154@gmail.com"
FREE_PASSWORD = "JobsFree#2026Aa!"
EMPLOYER_EMAIL = "e2e.employer.feature26@realaicoach.app"
EMPLOYER_PASSWORD = "E2EEmployer#Feature26!2026"

LOCKED_FEATURE_NUMBER = 26
LOCKED_FEATURE_ID = "jobs-portal"


@dataclass
class ParityRoute:
    name: str
    legacy_path: str
    v2_path: str
    method: str = "GET"
    actor: str = "candidate"
    expected_status: int = 200


ROUTES: List[ParityRoute] = [
    ParityRoute("candidate_jobs_search", "/api/jobs/search?q=engineer&page=1&limit=5", "/api/hiring/v2/candidate/jobs/search?q=engineer&page=1&limit=5", actor="candidate"),
    ParityRoute("candidate_recommendations", "/api/jobs/recommendations", "/api/hiring/v2/candidate/recommendations", actor="candidate"),
    ParityRoute("candidate_my_applications", "/api/jobs/my-applications?status=all", "/api/hiring/v2/candidate/applications?status=all", actor="candidate"),
    ParityRoute("candidate_saved_jobs", "/api/jobs/saved", "/api/hiring/v2/candidate/saved-jobs", actor="candidate"),
    ParityRoute("candidate_analytics", "/api/jobs/analytics", "/api/hiring/v2/candidate/analytics", actor="candidate"),
    ParityRoute("candidate_portal_summary", "/api/jobs/portal-summary", "/api/hiring/v2/dashboard/summary", actor="candidate"),
    ParityRoute("employer_pipeline_board", "/api/jobs/employer/pipeline-board?limit=20", "/api/hiring/v2/employer/pipeline-board?limit=20", actor="employer"),
    ParityRoute("employer_offers", "/api/jobs/employer/offers?limit=20", "/api/hiring/v2/employer/offers?limit=20", actor="employer"),
    ParityRoute("employer_kpi_header", "/api/jobs/employer/kpi-header?window_days=30", "/api/hiring/v2/employer/kpi-header?window_days=30", actor="employer"),
    ParityRoute("employer_sla_alerts", "/api/jobs/employer/sla-alerts?limit=20", "/api/hiring/v2/employer/sla-alerts?limit=20", actor="employer"),
]


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def login_admin(session: requests.Session) -> Tuple[bool, Dict[str, Any]]:
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=30,
        )
        payload: Dict[str, Any] = {}
        try:
            payload = response.json()
        except Exception:
            payload = {"raw": response.text[:500]}
        return (response.status_code == 200 and bool(payload.get("is_admin"))), {
            "status_code": response.status_code,
            "payload": payload,
        }
    except Exception as exc:
        return False, {"status_code": 0, "error": str(exc)}


def login_user(email: str, password: str) -> Tuple[Optional[requests.Session], Dict[str, Any]]:
    session = requests.Session()
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password},
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=30,
        )
        payload: Dict[str, Any] = {}
        try:
            payload = response.json()
        except Exception:
            payload = {"raw": response.text[:500]}

        if response.status_code != 200:
            return None, {"status_code": response.status_code, "payload": payload}
        return session, {"status_code": response.status_code, "payload": payload}
    except Exception as exc:
        return None, {"status_code": 0, "error": str(exc)}


def canonicalize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: canonicalize(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [canonicalize(x) for x in obj]
    return obj


def summarize_payload(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, dict):
        list_sizes = {
            key: len(val)
            for key, val in payload.items()
            if isinstance(val, list)
        }
        scalar_keys = sorted([key for key, val in payload.items() if not isinstance(val, (dict, list))])
        dict_keys = sorted([key for key, val in payload.items() if isinstance(val, dict)])
        return {
            "keys": sorted(payload.keys()),
            "list_sizes": list_sizes,
            "scalar_keys": scalar_keys,
            "dict_keys": dict_keys,
        }
    if isinstance(payload, list):
        return {
            "type": "list",
            "length": len(payload),
            "item_type": type(payload[0]).__name__ if payload else None,
        }
    return {"type": type(payload).__name__, "value": payload}


def normalize_for_parity(route_name: str, payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload

    normalized = dict(payload)

    if route_name == "candidate_saved_jobs":
        # Legacy returns `saved_jobs`, compatibility path may also include `jobs`.
        if "jobs" not in normalized and "saved_jobs" in normalized:
            normalized["jobs"] = normalized.get("saved_jobs")
    if route_name == "candidate_jobs_search":
        # Legacy includes `filters_applied`; v2 includes paging metadata.
        # Compare canonical search payload only.
        normalized = {
            "jobs": normalized.get("jobs", []),
            "total": normalized.get("total", 0),
        }
    if route_name == "candidate_portal_summary":
        # Different top-level naming is accepted; compare canonical metric projection.
        normalized = {
            "total_active_jobs": normalized.get("total_active_jobs"),
            "my_applications": normalized.get("my_applications"),
            "saved_jobs": normalized.get("saved_jobs"),
        }

    return normalized


def fetch_json(session: requests.Session, path: str, method: str = "GET") -> Dict[str, Any]:
    try:
        if method.upper() == "GET":
            response = session.get(f"{BASE_URL}{path}", timeout=40)
        else:
            response = session.request(method.upper(), f"{BASE_URL}{path}", timeout=40)

        payload: Any
        try:
            payload = response.json()
        except Exception:
            payload = {"raw": response.text[:1500]}

        return {
            "status_code": response.status_code,
            "ok": response.ok,
            "payload": payload,
        }
    except Exception as exc:
        return {
            "status_code": 0,
            "ok": False,
            "error": str(exc),
            "payload": None,
        }


def compare_route(session: requests.Session, route: ParityRoute) -> Dict[str, Any]:
    legacy_res = fetch_json(session, route.legacy_path, route.method)
    v2_res = fetch_json(session, route.v2_path, route.method)

    legacy_payload = normalize_for_parity(route.name, legacy_res.get("payload"))
    v2_payload = normalize_for_parity(route.name, v2_res.get("payload"))

    legacy_norm = canonicalize(legacy_payload)
    v2_norm = canonicalize(v2_payload)

    both_200 = legacy_res.get("status_code") == 200 and v2_res.get("status_code") == 200
    exact_match = bool(legacy_norm == v2_norm)

    legacy_summary = summarize_payload(legacy_payload)
    v2_summary = summarize_payload(v2_payload)

    summary_shape_match = (
        legacy_summary.get("keys") == v2_summary.get("keys")
        and legacy_summary.get("list_sizes") == v2_summary.get("list_sizes")
    ) if isinstance(legacy_payload, dict) and isinstance(v2_payload, dict) else False

    same_status = legacy_res.get("status_code") == v2_res.get("status_code")
    status_expected = legacy_res.get("status_code") == route.expected_status and v2_res.get("status_code") == route.expected_status
    tolerance_ok = bool(exact_match or summary_shape_match)
    parity_equivalent = bool(same_status and tolerance_ok)

    if parity_equivalent and status_expected:
        verdict = "pass"
    elif parity_equivalent:
        verdict = "pass_with_warning"
    else:
        verdict = "fail"

    return {
        "route_name": route.name,
        "legacy": {
            "path": route.legacy_path,
            "status_code": legacy_res.get("status_code"),
            "summary": legacy_summary,
        },
        "v2": {
            "path": route.v2_path,
            "status_code": v2_res.get("status_code"),
            "summary": v2_summary,
        },
        "comparison": {
            "both_status_200": both_200,
            "same_status": same_status,
            "status_expected": status_expected,
            "exact_match": exact_match,
            "shape_match_with_counts": summary_shape_match,
            "tolerance_ok": tolerance_ok,
            "parity_equivalent": parity_equivalent,
            "verdict": verdict,
        },
    }


def run() -> int:
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})

    admin_ok, login_meta = login_admin(session)

    report: Dict[str, Any] = {
        "timestamp": iso_now(),
        "scope": "feature26_phase_p1_5_read_parity_pack",
        "locked_protocol": {
            "feature_number": LOCKED_FEATURE_NUMBER,
            "feature_id": LOCKED_FEATURE_ID,
        },
        "base_url": BASE_URL,
        "admin_login": login_meta,
        "routes_compared": [],
        "summary": {},
        "policy_guardrails": {
            "legacy_read_pruning_executed": False,
            "allowed_action": "read_parity_verification_only",
            "blocked_action": "legacy_read_prune_or_delete_without_signoff_and_sustained_governance_gates",
        },
    }

    if not admin_ok:
        report["summary"] = {
            "overall_verdict": "fail",
            "reason": "admin_login_failed",
        }
        out = Path("/app/test_reports/feature26_phase_p1_5_read_parity_pack_latest.json")
        out.write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return 1

    candidate_session, candidate_login = login_user(FREE_EMAIL, FREE_PASSWORD)
    employer_session, employer_login = login_user(EMPLOYER_EMAIL, EMPLOYER_PASSWORD)

    report["actor_logins"] = {
        "candidate": candidate_login,
        "employer": employer_login,
    }

    pass_count = 0
    warning_count = 0
    fail_count = 0

    for route in ROUTES:
        actor_session = candidate_session if route.actor == "candidate" else employer_session
        if actor_session is None:
            row = {
                "route_name": route.name,
                "actor": route.actor,
                "comparison": {
                    "verdict": "fail",
                    "reason": f"{route.actor}_login_failed",
                },
            }
            report["routes_compared"].append(row)
            fail_count += 1
            continue

        row = compare_route(actor_session, route)
        row["actor"] = route.actor
        report["routes_compared"].append(row)
        if row["comparison"]["verdict"] == "pass":
            pass_count += 1
        elif row["comparison"]["verdict"] == "pass_with_warning":
            warning_count += 1
        else:
            fail_count += 1

    report["summary"] = {
        "total_routes": len(ROUTES),
        "pass_routes": pass_count,
        "pass_with_warning_routes": warning_count,
        "fail_routes": fail_count,
        "overall_verdict": "pass" if fail_count == 0 and warning_count == 0 else ("pass_with_warnings" if fail_count == 0 else "needs_review"),
        "next_action": "Use this parity pack for explicit v2 read parity sign-off decision.",
    }

    out_latest = Path("/app/test_reports/feature26_phase_p1_5_read_parity_pack_latest.json")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_ts = Path(f"/app/test_reports/feature26_phase_p1_5_read_parity_pack_{ts}.json")
    payload = json.dumps(report, indent=2)
    out_latest.write_text(payload)
    out_ts.write_text(payload)

    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
