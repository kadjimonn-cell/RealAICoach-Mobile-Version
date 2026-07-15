# V2 Teal Theme Compliance Ratchet

This repository enforces a **one-way ratchet** on theme debt. The current
baseline is checked in at `/app/.theme-baseline.json`. Any PR that raises
`warns` / `fails` above that baseline, or drops the overall grade, fails
the `V2 Teal Theme Compliance Gate` CI job and is blocked from merging.

## Current Baseline

Run `cat .theme-baseline.json` to see live values. As of the last lock:

| Metric | Value |
|---|---|
| Grade | A |
| Warns | 380 |
| Fails | 0 |
| Files scanned | 507 |
| Files clean | 282 |

## How to run locally

```bash
# Check if your branch passes the gate (exits 1 on regression)
python backend/scripts/theme_gate.py

# Print the delta report but don't fail (good for quick checks)
python backend/scripts/theme_gate.py --report-only

# After a successful cleanup pass, lower the baseline
python backend/scripts/theme_gate.py --update-baseline
git add .theme-baseline.json
git commit -m "chore(theme): lower baseline to $(jq .warns .theme-baseline.json) warns"
```

## How the gate works

1. The script imports `_build_theme_visibility_audit()` directly from
   `backend/routes/platform_perf.py` — the same static scan the admin
   dashboard runs.
2. It compares the current audit output to the committed baseline.
3. On regression (more warns, more fails, or lower grade), exits non-zero.
4. On GitHub Actions, this blocks the PR's merge button.

**No DB, no network, no secrets needed** — pure static analysis.

## How to reduce the baseline (the happy path)

1. Open the Admin Console → **Theme Compliance** page.
2. Click **"Auto-clean all safe offenders"** on the Top Offenders
   Leaderboard widget. The backend autofix service will transform hex
   literals and hex-concat alpha patterns into V2 Teal tokens.
3. Review the generated diffs, run `npx expo export` to verify compile.
4. Locally: `python backend/scripts/theme_gate.py --update-baseline`.
5. Commit both the transformed `.tsx` files AND the updated
   `.theme-baseline.json` in the same PR.
6. The gate will now permanently lock the lower threshold.

## Bypassing (intentionally raising the baseline)

The ONLY way to raise the baseline is to commit a new
`.theme-baseline.json`. If a non-regression is necessary (e.g. adding a
brand-new admin panel that temporarily adds warns while being iterated on),
the author must:

1. Explicitly run `--update-baseline` locally
2. Commit the new baseline file with a commit message explaining why
3. Get review approval for the baseline bump

This makes baseline increases visible in git history and code review,
rather than being silent drift.
