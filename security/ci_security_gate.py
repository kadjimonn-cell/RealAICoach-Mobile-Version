#!/usr/bin/env python3
"""Minimal CI security gate for RealAICoach hardening baseline."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]

IAP_SECRET_PATH_KEYS = [
    "ASC_PRIVATE_KEY_PATH",
    "APPLE_IAP_PRIVATE_KEY_PATH",
    "GOOGLE_PLAY_SERVICE_ACCOUNT_PATH",
    "GOOGLE_PLAY_IAP_SERVICE_ACCOUNT_PATH",
]
IAP_RUNTIME_ALLOWED_PREFIXES = ("/run/secrets/iap/", "/tmp/realaicoach/iap_secrets/")


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _read_env_value(path: str, key: str) -> str:
    env_file = ROOT / path
    if not env_file.exists():
        return ""
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return ""


def main() -> int:
    failures: list[str] = []

    middleware = _read("backend/middleware.py")
    policy_gate = _read("backend/utils/production_security_policy_gate.py")
    gitignore = _read(".gitignore")

    if '"/api/auth/",          # Auth flows (login, register, etc.)' in middleware:
        failures.append("CSRF gate too broad: '/api/auth/' blanket exemption still present")

    if "fallback_policy_gate_audit_secret_for_preview_only" in policy_gate:
        failures.append("Policy gate fallback secret must not exist")

    if ".env" not in gitignore:
        failures.append(".gitignore missing .env ignore patterns")

    disallowed_secret_files = [
        "backend/google_play_iap_service_account.json",
        "backend/google_play_service_account.json",
        "backend/AuthKey_34YP9488M8.p8",
        "backend/SubscriptionKey_848DFKTZ47.p8",
        "frontend/cookies.txt",
    ]
    for rel in disallowed_secret_files:
        if (ROOT / rel).exists():
            failures.append(f"Sensitive file must not exist in workspace: {rel}")

    for key in IAP_SECRET_PATH_KEYS:
        value = _read_env_value("backend/.env", key)
        if not value:
            continue
        if value.startswith("/app/backend/"):
            failures.append(f"{key} must not point to workspace path: {value}")
        elif not value.startswith(IAP_RUNTIME_ALLOWED_PREFIXES):
            failures.append(f"{key} must point to secure runtime mount path: {value}")

    try:
        tracked_env = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "backend/.env", "frontend/.env"],
            check=False,
            text=True,
            capture_output=True,
        ).stdout.strip()
        if tracked_env:
            failures.append("Tracked env files detected in git index (backend/.env or frontend/.env)")
    except Exception:
        failures.append("Unable to validate tracked env files with git")

    if failures:
        print("SECURITY_GATE=FAIL")
        for item in failures:
            print(f" - {item}")
        return 1

    print("SECURITY_GATE=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
