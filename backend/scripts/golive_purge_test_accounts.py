"""Go-live purge: delete test/E2E-pattern accounts from the target database.

DRY-RUN by default; pass --execute to actually delete. Run against production
by setting MONGO_URL/DB_NAME env vars (or after deploy, from the prod container).
Never deletes admins or explicitly protected emails.
"""

import os
import re
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/backend/.env")

TEST_PATTERN = re.compile(
    r"(@example\.com$|e2e|playwright|\.test\.|test\.|fixture|seed|\.iter\d+|watchvideos\.|shadowops\.|legends\.test|f21\.|feature21|feature26|tv\.(free|basic|premium)\.test|p1\.free)",
    re.I,
)
PROTECTED = {"admin@realaicoach.app"}


def main() -> None:
    execute = "--execute" in sys.argv
    client = MongoClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    targets = []
    for u in db.users.find({}, {"email": 1, "user_id": 1, "is_admin": 1, "_id": 0}):
        email = str(u.get("email") or "")
        if email in PROTECTED:
            continue
        if u.get("is_admin") and not TEST_PATTERN.search(email):
            continue
        if TEST_PATTERN.search(email):
            targets.append(u)

    print(f"{'EXECUTE' if execute else 'DRY-RUN'}: {len(targets)} test-pattern accounts identified")
    for u in targets[:20]:
        print(" ", u.get("email"))
    if len(targets) > 20:
        print(f"  ... and {len(targets) - 20} more")

    if not execute:
        print("\nPass --execute to delete. Related per-user data in other collections is retained (orphaned).")
        return

    emails = [u["email"] for u in targets]
    user_ids = [u.get("user_id") for u in targets if u.get("user_id")]
    result = db.users.delete_many({"email": {"$in": emails}})
    db.subscription_audit_log.insert_one(
        {
            "event_type": "golive_test_account_purge",
            "deleted_count": result.deleted_count,
            "user_ids_sample": user_ids[:50],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    print(f"Deleted {result.deleted_count} accounts (audit logged).")


if __name__ == "__main__":
    main()
