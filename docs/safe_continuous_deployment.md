# Safe Continuous Deployment Guide

This document outlines the strategies and practices for safely deploying changes to the RealAICoach application.

## 1. Feature Flags & Premium Guards

We use a feature flagging system to safely roll out new features.

-   **PremiumGuard:** Wrap new, high-risk, or paid features in the `<PremiumGuard>` component. This allows us to control access based on user subscription status.
    ```tsx
    <PremiumGuard featureName="New Feature">
      <NewFeatureComponent />
    </PremiumGuard>
    ```
-   **ConfigContext:** Use `ConfigContext` for system-wide flags that can be toggled via backend response.

## 2. Environment Variables

-   **Never Hardcode:** All API URLs, Keys, and Secrets must be in `.env` files.
-   **Production vs. Development:** Ensure `REACT_APP_BACKEND_URL` points to the correct environment.
-   **Validation:** The app checks for critical environment variables on startup.

## 3. Testing Strategy

### Smoke Tests
Before any deployment, run the Smoke Test suite:
1.  Navigate to `/smoke-test` in the app.
2.  Run the test to validate core routes (Welcome, Login, Home).
3.  Ensure all statuses are `PASS`.

### Automated Testing
-   **Backend:** Run `pytest` for API endpoint verification.
-   **Frontend:** Use `jest` and `react-test-renderer` for component snapshots.

## 4. Database Migrations

-   **Non-Destructive Changes:** Always add fields, never rename or remove them in a way that breaks running code.
-   **Backward Compatibility:** Ensure the backend can handle both old and new schema formats during the rollout.

## 5. Rollback Plan

If a critical bug is discovered:
1.  **Revert:** Use the platform's "Rollback" feature to revert to the previous stable commit.
2.  **Feature Switch:** If the bug is isolated to a feature behind a flag, disable that feature via the backend config without a full redeploy.

## 6. Monitoring & Logs

-   **Supervisor:** Check `/var/log/supervisor/` for backend (`backend.err.log`) and frontend (`expo.err.log`) errors.
-   **Error Boundaries:** The React Native app has a global Error Boundary to catch crashes and display a fallback UI.


## 7. Scheduled Tasks & Automation

-   **APScheduler:** We use `APScheduler` (AsyncIO) in `server.py` for background tasks.
-   **Startup/Shutdown:** The scheduler lifecycle is tied to the FastAPI app events (`startup` and `shutdown`).
-   **Idempotency:** Scheduled jobs should be idempotent (safe to run multiple times) to handle restarts or multiple instances gracefully.

## 7. Deployment Checklist

- [ ] Linting passed (`yarn lint`)
- [ ] TypeScript types checked (`tsc`)
- [ ] Smoke tests passed
- [ ] Environment variables verified
- [ ] Database backup taken (if schema changes involved)
