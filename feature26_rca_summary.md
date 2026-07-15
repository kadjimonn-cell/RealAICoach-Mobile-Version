# Feature 26 Root-Cause Analysis - PASS ✅

**Test Date**: 2026-06-17 23:33 UTC  
**Protocol**: feature_number=26, feature_id=jobs-portal  
**Base URL**: https://visa-polish-v2.preview.emergentagent.com  
**Admin**: admin@realaicoach.app / NewAdminPass2026!

---

## Executive Summary

✅ **ROOT CAUSE CONFIRMED**: Test/synthetic legacy telemetry contamination combined with strict all-window gate criteria.

### Key Finding

When `exclude_synthetic=true` is applied in **near_zero mode**, the system transitions from:
- ❌ `sustained_gate_met: false` → ✅ `sustained_gate_met: true`
- ❌ `ready_for_legacy_code_removal: false` → ✅ `ready_for_legacy_code_removal: true`

This confirms that **synthetic/test data is artificially inflating legacy telemetry metrics**, preventing the system from recognizing that legacy routes are ready for retirement.

---

## Detailed Test Results

### 1. STRICT_ZERO Mode (max_events=0, max_active_users=0)

#### With Synthetic Data (`exclude_synthetic=false`)
- **sustained_gate_met**: `false` ❌
- **ready_for_legacy_code_removal**: `false` ❌
- **jobs.72h.total_events**: 17 (raw: 17, synthetic_excluded: 0)
- **jobs.72h.active_users**: 2
- **employers.72h.total_events**: 2 (raw: 2, synthetic_excluded: 0)
- **employers.72h.active_users**: 1

#### Without Synthetic Data (`exclude_synthetic=true`)
- **sustained_gate_met**: `false` ❌
- **ready_for_legacy_code_removal**: `false` ❌
- **jobs.72h.total_events**: 2 (raw: 17, **synthetic_excluded: 15**)
- **jobs.72h.active_users**: 1
- **employers.72h.total_events**: 2 (raw: 2, synthetic_excluded: 0)
- **employers.72h.active_users**: 1

**Analysis**: Even with synthetic exclusion, strict_zero mode still fails because there are 2 real events and 1 active user in the jobs family. Strict_zero requires **exactly 0 events and 0 users**.

---

### 2. NEAR_ZERO Mode (max_events=5, max_active_users=2)

#### With Synthetic Data (`exclude_synthetic=false`)
- **sustained_gate_met**: `false` ❌
- **ready_for_legacy_code_removal**: `false` ❌
- **jobs.72h.total_events**: 17 (raw: 17, synthetic_excluded: 0)
- **jobs.72h.active_users**: 2
- **jobs.72h.gate_met**: `false` (exceeds max_events=5)
- **employers.72h.total_events**: 2 (raw: 2, synthetic_excluded: 0)
- **employers.72h.active_users**: 1
- **employers.72h.gate_met**: `true` ✅

**Failing Windows**: All windows (72h, 7d, 14d, 30d) fail due to jobs family exceeding threshold

#### Without Synthetic Data (`exclude_synthetic=true`)
- **sustained_gate_met**: `true` ✅
- **ready_for_legacy_code_removal**: `true` ✅
- **jobs.72h.total_events**: 2 (raw: 17, **synthetic_excluded: 15**)
- **jobs.72h.active_users**: 1
- **jobs.72h.gate_met**: `true` ✅ (within max_events=5, max_active_users=2)
- **employers.72h.total_events**: 2 (raw: 2, synthetic_excluded: 0)
- **employers.72h.active_users**: 1
- **employers.72h.gate_met**: `true` ✅

**Failing Windows**: None - all windows pass ✅

**Recommended Action**: "Safe to remove legacy write routes for /api/jobs and /api/employers."

---

### 3. Deprecation Telemetry (14-day lookback)

- **Total Events**: 19
- **Active Legacy Users**: 2
- **Migration Progress**: 92.0%
- **Remaining Legacy Operations**:
  1. `candidate_save_job` - 17 events
  2. `employers_reverify` - 2 events

#### Top Legacy Endpoints
1. `/api/jobs/save/test_job_nonexistent_12345` - 5 events
2. `/api/jobs/save/test_telemetry_job_12345` - 4 events
3. `/api/jobs/save/job_admin_test_123` - 3 events
4. `/api/jobs/save/job_metadata_test` - 2 events
5. `/api/employers/reverify` - 2 events

#### User Analysis
- **user_798c19018cad**: 15 events (test/synthetic user)
- **user_4b5a68d2f7c6**: 4 events (admin user)

**Key Observation**: The majority of legacy events (15 out of 17 for jobs) are from a single test/synthetic user (`user_798c19018cad`), confirming that test activity is contaminating the telemetry.

---

## Root Cause Confirmation

### ✅ PASS - Root Cause Verified

**Root Cause**: Test/synthetic legacy telemetry contamination combined with strict all-window gate criteria.

### Evidence

1. **Synthetic Data Impact**:
   - 15 out of 17 jobs events are synthetic (88% contamination)
   - When excluded, jobs family drops from 17 events → 2 events
   - Active users drop from 2 → 1

2. **Mode Sensitivity**:
   - **strict_zero**: Too strict - requires exactly 0 events/users (fails even with real traffic)
   - **near_zero**: Appropriate threshold - allows minimal real traffic (≤5 events, ≤2 users)

3. **Gate Behavior**:
   - With synthetic data: `near_zero` fails due to 17 events exceeding threshold
   - Without synthetic data: `near_zero` passes with 2 events within threshold
   - All 4 time windows (72h, 7d, 14d, 30d) show consistent behavior

4. **Sustained Gate Requirement**:
   - System requires ALL windows to pass for `sustained_gate_met=true`
   - Single failing window blocks legacy code removal
   - Synthetic contamination causes all windows to fail in near_zero mode

---

## Recommendations

### Immediate Actions

1. **Use `exclude_synthetic=true` for Production Decisions**:
   - Production readiness should be evaluated with synthetic data excluded
   - Current telemetry shows system is ready for legacy removal when synthetic data is filtered

2. **Adopt `near_zero` Mode for Production Gates**:
   - `strict_zero` is too strict for real-world scenarios
   - `near_zero` (≤5 events, ≤2 users) provides appropriate safety margin
   - Allows minimal real traffic while preventing premature removal

3. **Implement Synthetic User Tagging**:
   - Ensure all test/E2E users are properly tagged as synthetic
   - Current tagging appears effective (15/17 events correctly identified)
   - Verify `user_798c19018cad` is properly marked as synthetic

4. **Monitor Real User Activity**:
   - 2 real jobs events from 1 user in 72h window
   - 2 employers events from 1 user in 72h window
   - Low but non-zero real traffic - appropriate for near_zero threshold

### Long-term Improvements

1. **Automated Synthetic Filtering**:
   - Default to `exclude_synthetic=true` for production telemetry
   - Provide `include_synthetic=true` option for debugging only

2. **Graduated Thresholds**:
   - Consider time-based threshold relaxation (stricter for recent windows)
   - Allow different thresholds per route family based on criticality

3. **User Classification**:
   - Maintain clear separation between test/synthetic and real users
   - Regular audit of user classification accuracy

---

## Conclusion

**PASS** ✅ - Root cause successfully confirmed through read-only verification.

The system's legacy removal readiness is being blocked by test/synthetic telemetry contamination. When synthetic data is properly excluded using `exclude_synthetic=true` in `near_zero` mode, the system correctly identifies that legacy routes are ready for removal across all time windows (72h, 7d, 14d, 30d).

**Production Recommendation**: Enable legacy code removal using `mode=near_zero` with `exclude_synthetic=true`.

---

## Test Artifacts

- **Full Results**: `/app/feature26_rca_results.json`
- **Test Script**: `/app/feature26_rca_test.py`
- **Test Date**: 2026-06-17 23:33:40 UTC
