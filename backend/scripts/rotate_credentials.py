"""One-time credential rotation for go-live. Rotates documented dev/test/admin passwords,
bumps token_version (invalidates sessions), and audit-logs each rotation."""

import json
import os
import sys
from datetime import datetime, timezone

import bcrypt
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/backend/.env")

ROTATIONS_FILE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/rotations.json"


def main() -> None:
    rotations = json.load(open(ROTATIONS_FILE))  # {email: new_password}
    client = MongoClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    now_iso = datetime.now(timezone.utc).isoformat()

    rotated, missing = [], []
    for email, new_pw in rotations.items():
        user = db.users.find_one({"email": email}, {"user_id": 1})
        if not user:
            missing.append(email)
            continue
        new_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
        db.users.update_one(
            {"email": email},
            {"$set": {"password_hash": new_hash, "updated_at": now_iso}, "$inc": {"token_version": 1}},
        )
        db.subscription_audit_log.insert_one(
            {"event_type": "credential_rotation", "email": email, "reason": "go-live rotation", "created_at": now_iso}
        )
        rotated.append(email)

    print(f"Rotated {len(rotated)} accounts: {rotated}")
    if missing:
        print(f"NOT FOUND (skipped): {missing}")


if __name__ == "__main__":
    main()
