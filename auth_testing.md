# Auth Fallback + Platform Health Testing Playbook

## Scope
- Password login fallback
- Magic link fallback
- QR login fallback
- SSO redirect integrity guardrails
- Platform health (API/static/routes/responsive)

## Backend API checks
1. `POST /api/auth/login` with valid email/password should return `session_token`.
2. `POST /api/auth/magic-link/send` should return success and write `auth_base` in `magic_links`.
3. `POST /api/auth/qr/generate` should return `qr_url` using canonical fallback base.
4. `GET /api/auth/sso-config` should report Microsoft/Apple callback registration booleans.
5. `GET /api/auth/admin/fallback-links/health` should return active base + stale counters.
6. `POST /api/auth/admin/sso-validate-e2e` should pass in strict mode.
7. `POST /api/auth/password/reset/request` should not return 500 for valid email.
8. `POST /api/auth/password/reset/confirm` should:
   - return 200 for valid token
   - return 400 for invalid/expired token
   - never return 500 (datetime compare guard)
9. `POST /api/auth/token/refresh` should issue fresh session token where applicable.
10. `GET /api/auth/me` should return user for valid session and 401 otherwise.

## Data/integrity checks
- `users.email` has unique index
- `password_reset_tokens.expires_at` has TTL index
- `login_attempts.identifier` index exists
- password hash format starts with `$2b$`

## QR E2E flow
1. Create QR session (`/auth/qr/generate`).
2. Approve same session as authenticated user (`/auth/qr/approve`).
3. Poll status (`/auth/qr/status/{session_id}`) and verify approved token returned once.

## Platform health checks
- `/`, `/welcome`, `/auth/login`, `/api/health`
- `/api/admin/platform-integrity/overview`
- `/api/admin/platform-perf/dashboard?period=1h`
- Manifest + favicon + apple-touch-icon + all PWA icons return 200.

## Frontend checks
- No blank screen on welcome/login/admin pages.
- Fallback panel options visible when SSO diagnostics enters fallback.
- Responsive rendering: mobile (390x844), tablet (768x1024), desktop (1920x1080).

## Progressive Risk Engine (P0) checks
1. `POST /api/auth/login`
   - MEDIUM/HIGH risk should return `requires_2fa: true` + `risk_level`, `risk_score`, `risk_output`.
   - CRITICAL risk should return `403` with `code: risk_engine_id_verification_required`.
2. `POST /api/auth/otp/verify` and `POST /api/auth/2fa/verify`
   - Session documents include `mfa_verified_at` and `risk_context`.
   - CRITICAL risk should block session issuance and trigger ID verification.
3. `GET /api/admin/executive/risk-control`
   - Returns `risk_engine.output_block` in required format:
     - `RISK_ENGINE_STATUS`
     - `RISK_SCORE`
     - `RISK_LEVEL`
     - `TRIGGER`
     - `FALSE_POSITIVE_RATE`
     - `SESSION_PROTECTION`
     - `CONFIDENCE`
4. `POST /api/admin/executive/risk-actions`
   - `lock_session` invalidates target sessions.
   - `force_id_verification` marks/creates pending IDV.
   - `clear_admin_block` stores admin override for risk profile.
5. Admin containment
   - For HIGH/CRITICAL risk admin profiles, privileged admin APIs should return `403 risk_engine_admin_api_blocked`.

## Payments config public exact guard
1. `GET /api/payments/config` without auth should return `200` and only public client configuration.
2. `GET /api/payments/cards` without auth should still return `401 AUTH_REQUIRED`.

## Payment recovery stats admin guard
1. `GET /api/subscriptions/recovery-stats` with a non-admin authenticated user should return `403 Admin access required`.
2. `GET /api/subscriptions/recovery-stats` with an admin token should return `200` and the recovery analytics payload.

## Auth brute-force and admin seed guard
1. Six consecutive failed `POST /api/auth/login` attempts from one source should produce an active security block; the post-threshold response should be `403`.
2. `ensure_admin_users()` should rotate an existing admin password hash when `ADMIN_PASSWORD` is set and no longer matches the stored hash.
