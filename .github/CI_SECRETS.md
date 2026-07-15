# CI Secrets — Setup Guide

The CI pipelines (`.github/workflows/ci-quality-gate.yml`, `regression.yml`) require **two GitHub repository secrets** so that the field-level encryption + HMAC-lookup code paths work in CI. These are distinct from your production keys — they only run against the ephemeral MongoDB service container inside the GitHub runner.

## Secrets to provision

Navigate to:
**GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

Add exactly these two:

| Secret name                | Purpose                                      | Suggested value (CI-only, rotate any time) |
|----------------------------|----------------------------------------------|---------------------------------------------|
| `FIELD_ENCRYPTION_KEY_CI`  | Fernet key for `enc:` field-level encryption | `331YxKsc5chc6b9WceFcdTVID-w0oTxQKMBaP8x3898=` |
| `FIELD_LOOKUP_HMAC_KEY_CI` | HMAC-SHA256 key for deterministic `email_hash` lookups | `q2unQl7nCHRRJ5IkfXa4YH_YlghHld7d4KXBohDJ4KRqdz4tuuaaWKqD6ZeL595K` |

> **Important** — These sample values above are generated for convenience. Replace them with your own before committing, using:
>
> ```bash
> python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"   # FIELD_ENCRYPTION_KEY_CI
> python3 -c "import secrets; print(secrets.token_urlsafe(48))"                                # FIELD_LOOKUP_HMAC_KEY_CI
> ```

## Why they're required

- `FIELD_ENCRYPTION_KEY` — without it, any test that touches encrypted fields (MFA, KYC, PII on contact/support/feedback) will throw `RuntimeError: FIELD_ENCRYPTION_KEY environment variable is not set` at import time, failing every regression suite.
- `FIELD_LOOKUP_HMAC_KEY` — drives `hash_lookup()` for GDPR email-hash matching, the admin search path, and the retention purge. Without it the GDPR lifecycle + retention pytest suites fail.

## Never reuse production keys in CI

CI runs against a throwaway MongoDB container seeded with pytest fixtures. The CI keys never encrypt real user data — they're regenerable. Use fresh values distinct from `/app/backend/.env`.

## Verify after provisioning

Push any commit to a PR and check the **Regression** workflow run:

```
~ Running theme visibility audit (min grade = A)...
✓ Theme audit: grade=A fails=0
~ Running pytest suites...
✓ 13 tests passed in N.NNs
✓ All regression checks passed.
```

If the workflow still fails with `KeyError: 'FIELD_ENCRYPTION_KEY'` or similar, re-check that both secrets are set at **repo level** (not org level) with **exact spelling + `_CI` suffix**.
