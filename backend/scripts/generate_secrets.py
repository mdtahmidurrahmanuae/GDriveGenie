"""
Run this once to set up the dashboard PIN and generate all secrets.
Secrets are stored directly in the Cloudflare D1 database — no .env file required.

Required environment variables:
    CF_ACCOUNT_ID       — Cloudflare account ID
    CF_D1_DATABASE_ID   — D1 database ID
    CF_API_TOKEN        — Cloudflare API token with D1:Edit permission

Usage:
    python backend/scripts/generate_secrets.py
"""
import os
import secrets
import sys

import bcrypt
import httpx
from cryptography.fernet import Fernet

CF_ACCOUNT_ID = os.environ["CF_ACCOUNT_ID"]
CF_D1_DATABASE_ID = os.environ["CF_D1_DATABASE_ID"]
CF_API_TOKEN = os.environ["CF_API_TOKEN"]

_BASE = (
    f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}"
    f"/d1/database/{CF_D1_DATABASE_ID}/query"
)
_HEADERS = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json",
}


def d1_execute(sql: str, params: list | None = None) -> list[dict]:
    payload = {"sql": sql}
    if params:
        payload["params"] = params
    resp = httpx.post(_BASE, headers=_HEADERS, json=payload)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"D1 error: {data.get('errors')}")
    return data["result"][0].get("results", [])


def setup_table() -> None:
    d1_execute("""
        CREATE TABLE IF NOT EXISTS app_config (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)


def upsert(key: str, value: str) -> None:
    d1_execute(
        "INSERT INTO app_config (key, value) VALUES (?, ?)"
        " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        [key, value],
    )


def already_has_secrets() -> bool:
    try:
        rows = d1_execute("SELECT COUNT(*) AS n FROM app_config")
        return bool(rows and rows[0].get("n", 0) > 0)
    except Exception:
        return False


def main() -> None:
    setup_table()

    if already_has_secrets():
        print("Secrets already exist in D1.")
        overwrite = input("Regenerate them? [y/N] ").strip().lower()
        if overwrite != "y":
            print("Aborted — existing secrets unchanged.")
            sys.exit(0)

    pin = input("Enter your dashboard PIN: ").strip()
    if not pin:
        print("PIN cannot be empty.")
        sys.exit(1)

    pin_hash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()
    jwt_secret = secrets.token_urlsafe(32)
    encryption_key = Fernet.generate_key().decode()

    upsert("dashboard_pin_hash", pin_hash)
    upsert("jwt_secret", jwt_secret)
    upsert("encryption_key", encryption_key)

    print("\nSecrets saved to Cloudflare D1.")
    print("You can now start the backend:\n")
    print("    uvicorn main:app --reload")


if __name__ == "__main__":
    main()
