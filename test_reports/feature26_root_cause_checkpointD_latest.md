# Feature 26 Root Cause — Checkpoint D (Current Codebase, Locked Protocol)

- Timestamp: 2026-06-18T10:35:27.670992Z
- feature_number=26, feature_id=jobs-portal

## Gate Comparison
- strict_zero_exclude_synthetic_false: sustained=False, ready=False, divergence=True
- near_zero_exclude_synthetic_false: sustained=False, ready=False, divergence=True
- near_zero_exclude_synthetic_true: sustained=True, ready=True, divergence=False

## Root Cause Confirmed
1. Governance readiness remains blocked because strict/near gates with synthetic included are not sustained across all required windows.
2. Residual jobs/employers legacy telemetry (`candidate_save_job`, `employers_reverify`) keeps `sustained_gate_met=false` in governance view.
3. Operational near_zero excluding synthetic remains green, but policy uses governance gates for retirement approval, creating divergence.

## Remaining for DONE
- Sustained governance gate pass required across all windows under approved policy mode.
- Explicit v2 read parity sign-off required before any read-route retirement action.
- Feature tracker row #26 remains Pending Verification until policy criteria are satisfied and user issues final completion approval.
- Continue mandatory free-user non-OTP admin-block check in each cycle with passing evidence artifacts.

## Guardrail
- No legacy read-route pruning/deletion executed in this checkpoint.
