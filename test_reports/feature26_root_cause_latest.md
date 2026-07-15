# Feature 26 Root Cause Checkpoint A (Locked Protocol)

- Timestamp: 2026-06-17T23:31:47.503438Z
- feature_number=26, feature_id=jobs-portal

## Gate Comparison
- strict_zero exclude_synthetic=false: {'sustained_gate_met': False, 'ready_for_legacy_code_removal': False, 'failing_windows_count': 4, 'jobs_72h': {'total_events': 17, 'raw_total_events': 17, 'synthetic_excluded_count': 0, 'active_users': 2, 'gate_met': False}, 'employers_72h': {'total_events': 2, 'raw_total_events': 2, 'synthetic_excluded_count': 0, 'active_users': 1, 'gate_met': False}}
- strict_zero exclude_synthetic=true: {'sustained_gate_met': False, 'ready_for_legacy_code_removal': False, 'failing_windows_count': 4, 'jobs_72h': {'total_events': 2, 'raw_total_events': 17, 'synthetic_excluded_count': 15, 'active_users': 1, 'gate_met': False}, 'employers_72h': {'total_events': 2, 'raw_total_events': 2, 'synthetic_excluded_count': 0, 'active_users': 1, 'gate_met': False}}
- near_zero exclude_synthetic=false: {'sustained_gate_met': False, 'ready_for_legacy_code_removal': False, 'failing_windows_count': 4, 'jobs_72h': {'total_events': 17, 'raw_total_events': 17, 'synthetic_excluded_count': 0, 'active_users': 2, 'gate_met': False}, 'employers_72h': {'total_events': 2, 'raw_total_events': 2, 'synthetic_excluded_count': 0, 'active_users': 1, 'gate_met': True}}
- near_zero exclude_synthetic=true: {'sustained_gate_met': True, 'ready_for_legacy_code_removal': True, 'failing_windows_count': 0, 'jobs_72h': {'total_events': 2, 'raw_total_events': 17, 'synthetic_excluded_count': 15, 'active_users': 1, 'gate_met': True}, 'employers_72h': {'total_events': 2, 'raw_total_events': 2, 'synthetic_excluded_count': 0, 'active_users': 1, 'gate_met': True}}

## Telemetry Signals
- 14d total_events=19, active_legacy_users=2
- 14d top_operations=[{'operation': 'candidate_save_job', 'count': 17}, {'operation': 'employers_reverify', 'count': 2}]
- 14d top_legacy_endpoints=[{'endpoint': '/api/jobs/save/test_job_nonexistent_12345', 'count': 5}, {'endpoint': '/api/jobs/save/test_telemetry_job_12345', 'count': 4}, {'endpoint': '/api/jobs/save/job_admin_test_123', 'count': 3}, {'endpoint': '/api/jobs/save/job_metadata_test', 'count': 2}, {'endpoint': '/api/employers/reverify', 'count': 2}, {'endpoint': '/api/jobs/save/job_test_p2_123', 'count': 2}, {'endpoint': '/api/jobs/save/test_job_12345', 'count': 1}]

## Root Cause
1. Legacy-removal gates remain blocked by residual deprecation telemetry, dominated by jobs-family candidate_save_job events.
2. Synthetic exclusion heuristics do not remove all test-generated legacy events (notably employers_reverify and some test-pattern variants), leaving non-zero counts even with exclude_synthetic=true.
3. Gate policy requires sustained all-window pass (72h/7d/14d/30d) for both families, so any residual events keep sustained_gate_met=false.
