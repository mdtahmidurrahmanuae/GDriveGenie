#!/usr/bin/env python3
"""
GDriveGenie PocketBase Setup Script
====================================
Run this ONCE to:
  1. Create all gdrive_* collections in your PocketBase instance
  2. Create the initial super-admin user
  3. Generate and print the required .env values

Usage:
  python backend/scripts/setup_pocketbase.py

You will be prompted for:
  - PocketBase admin email + password  (PocketBase system admin, not the app user)
  - PocketBase URL (default: https://data.genericxinus.com)
  - GDriveGenie super-admin email + password (the first app user)
"""

import json
import os
import secrets
import sys

import httpx
from cryptography.fernet import Fernet

PB_URL_DEFAULT = "https://data.genericxinus.com"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ask(prompt: str, default: str = "") -> str:
    full = f"{prompt} [{default}]: " if default else f"{prompt}: "
    val = input(full).strip()
    return val or default


def ask_secret(prompt: str) -> str:
    import getpass
    return getpass.getpass(f"{prompt}: ").strip()


def pb_admin_auth(client: httpx.Client, pb_url: str, email: str, password: str) -> str:
    """Try both old and new PocketBase admin auth endpoints. Returns token."""
    endpoints = [
        f"{pb_url}/api/collections/_superusers/auth-with-password",
        f"{pb_url}/api/admins/auth-with-password",
    ]
    for ep in endpoints:
        try:
            r = client.post(ep, json={"identity": email, "password": password})
            if r.status_code == 200:
                token = r.json().get("token", "")
                if token:
                    print(f"  ✓ PocketBase admin authenticated via {ep.split('/api/')[1]}")
                    return token
            elif r.status_code == 404:
                continue
            else:
                data = r.json()
                print(f"  Auth failed ({r.status_code}): {data.get('message', r.text)}")
        except Exception as e:
            print(f"  Error on {ep}: {e}")
    raise SystemExit("Could not authenticate with PocketBase. Check credentials and URL.")


def create_collection(client: httpx.Client, pb_url: str, token: str, schema: dict) -> dict:
    headers = {"Authorization": token}
    # Try to get existing
    name = schema["name"]
    indexes = schema.pop("indexes", [])
    r = client.get(f"{pb_url}/api/collections/{name}", headers=headers)
    if r.status_code == 200:
        print(f"  ✓ Collection '{name}' already exists — skipping")
        result = r.json()
    else:
        # Create without indexes first (PocketBase evaluates indexes before fields are ready)
        r = client.post(f"{pb_url}/api/collections", headers=headers, json=schema)
        if r.status_code not in (200, 204):
            raise SystemExit(f"Failed to create collection '{name}': {r.status_code} {r.text}")
        result = r.json()
        print(f"  ✓ Created collection '{name}'")
    # Always apply indexes (idempotent — PocketBase skips existing ones)
    if indexes:
        r_get = client.get(f"{pb_url}/api/collections/{name}", headers=headers)
        current = r_get.json()
        current["indexes"] = indexes
        r2 = client.patch(f"{pb_url}/api/collections/{name}", headers=headers, json=current)
        if r2.status_code in (200, 204):
            print(f"  ✓ Applied indexes to '{name}'")
        else:
            print(f"  ! Could not apply indexes to '{name}': {r2.status_code} {r2.text[:200]}")
    return result


def get_collection_id(client: httpx.Client, pb_url: str, token: str, name: str) -> str:
    headers = {"Authorization": token}
    r = client.get(f"{pb_url}/api/collections/{name}", headers=headers)
    r.raise_for_status()
    return r.json()["id"]


# ---------------------------------------------------------------------------
# Collection schemas
# ---------------------------------------------------------------------------

def build_schemas(users_id: str, accounts_id: str, files_id: str, folders_id: str) -> list[dict]:
    """
    Returns schemas in dependency order.
    Called after gdrive_users + gdrive_accounts + gdrive_files + gdrive_folders are created
    so we can fill in their IDs for relation fields.
    """
    return [
        # gdrive_folder_files
        {
            "name": "gdrive_folder_files",
            "type": "base",
            "schema": [
                {
                    "name": "folder",
                    "type": "relation",
                    "required": True,
                    "options": {
                        "collectionId": folders_id,
                        "cascadeDelete": True,
                        "minSelect": None,
                        "maxSelect": 1,
                        "displayFields": [],
                    },
                },
                {
                    "name": "file",
                    "type": "relation",
                    "required": True,
                    "options": {
                        "collectionId": files_id,
                        "cascadeDelete": True,
                        "minSelect": None,
                        "maxSelect": 1,
                        "displayFields": [],
                    },
                },
            ],
            "indexes": [
                "CREATE UNIQUE INDEX idx_gdrive_folder_files ON gdrive_folder_files (folder, file)"
            ],
            "listRule": None,
            "viewRule": None,
            "createRule": None,
            "updateRule": None,
            "deleteRule": None,
        },
        # gdrive_shares
        {
            "name": "gdrive_shares",
            "type": "base",
            "schema": [
                {
                    "name": "folder",
                    "type": "relation",
                    "required": True,
                    "options": {
                        "collectionId": folders_id,
                        "cascadeDelete": True,
                        "minSelect": None,
                        "maxSelect": 1,
                        "displayFields": [],
                    },
                },
                {
                    "name": "created_by",
                    "type": "relation",
                    "required": True,
                    "options": {
                        "collectionId": users_id,
                        "cascadeDelete": True,
                        "minSelect": None,
                        "maxSelect": 1,
                        "displayFields": [],
                    },
                },
                {
                    "name": "share_type",
                    "type": "select",
                    "required": True,
                    "options": {"maxSelect": 1, "values": ["user", "public", "password"]},
                },
                {
                    "name": "shared_with",
                    "type": "relation",
                    "required": False,
                    "options": {
                        "collectionId": users_id,
                        "cascadeDelete": False,
                        "minSelect": None,
                        "maxSelect": 1,
                        "displayFields": [],
                    },
                },
                {
                    "name": "password_hash",
                    "type": "text",
                    "required": False,
                    "options": {"min": None, "max": None, "pattern": ""},
                },
                {
                    "name": "token",
                    "type": "text",
                    "required": True,
                    "options": {"min": None, "max": None, "pattern": ""},
                },
                {
                    "name": "expires_at",
                    "type": "text",
                    "required": False,
                    "options": {"min": None, "max": None, "pattern": ""},
                },
            ],
            "indexes": [
                "CREATE UNIQUE INDEX idx_gdrive_shares_token ON gdrive_shares (token)"
            ],
            "listRule": None,
            "viewRule": None,
            "createRule": None,
            "updateRule": None,
            "deleteRule": None,
        },
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n=== GDriveGenie PocketBase Setup ===\n")

    pb_url = ask("PocketBase URL", PB_URL_DEFAULT).rstrip("/")
    pb_admin_email = ask("PocketBase admin email (system admin)")
    pb_admin_password = ask_secret("PocketBase admin password")

    print("\n[1] Authenticating with PocketBase...")
    with httpx.Client(timeout=30.0) as client:
        token = pb_admin_auth(client, pb_url, pb_admin_email, pb_admin_password)
        headers = {"Authorization": token}

        print("\n[2] Creating collections...")

        # --- gdrive_users (auth collection) ---
        users_schema = {
            "name": "gdrive_users",
            "type": "auth",
            "schema": [
                {"name": "display_name", "type": "text", "required": False, "options": {"min": None, "max": 200, "pattern": ""}},
                {"name": "bio", "type": "text", "required": False, "options": {"min": None, "max": 1000, "pattern": ""}},
                {"name": "storage_limit_bytes", "type": "number", "required": False, "options": {"min": 0, "max": None, "noDecimal": True}},
                {"name": "storage_used_bytes", "type": "number", "required": False, "options": {"min": 0, "max": None, "noDecimal": True}},
                {"name": "is_super_admin", "type": "bool", "required": False, "options": {}},
                {"name": "avatar_drive_file_id", "type": "text", "required": False, "options": {"min": None, "max": None, "pattern": ""}},
                {"name": "avatar_account_id", "type": "text", "required": False, "options": {"min": None, "max": None, "pattern": ""}},
            ],
            "options": {
                "allowEmailAuth": True,
                "allowOAuth2Auth": False,
                "allowUsernameAuth": False,
                "exceptEmailDomains": [],
                "manageRule": None,
                "minPasswordLength": 8,
                "onlyEmailDomains": [],
                "requireEmail": True,
            },
            "indexes": [],
            "listRule": None,
            "viewRule": None,
            "createRule": None,
            "updateRule": None,
            "deleteRule": None,
        }
        create_collection(client, pb_url, token, users_schema)
        users_id = get_collection_id(client, pb_url, token, "gdrive_users")

        # --- gdrive_accounts ---
        accounts_schema = {
            "name": "gdrive_accounts",
            "type": "base",
            "schema": [
                {
                    "name": "user",
                    "type": "relation",
                    "required": True,
                    "options": {
                        "collectionId": users_id,
                        "cascadeDelete": True,
                        "minSelect": None,
                        "maxSelect": 1,
                        "displayFields": [],
                    },
                },
                {"name": "account_index", "type": "number", "required": True, "options": {"min": 1, "max": None, "noDecimal": True}},
                {"name": "email", "type": "text", "required": False, "options": {"min": None, "max": None, "pattern": ""}},
                {"name": "refresh_token_encrypted", "type": "text", "required": False, "options": {"min": None, "max": None, "pattern": ""}},
                {"name": "access_token", "type": "text", "required": False, "options": {"min": None, "max": None, "pattern": ""}},
                {"name": "token_expiry", "type": "text", "required": False, "options": {"min": None, "max": None, "pattern": ""}},
                {"name": "is_connected", "type": "bool", "required": False, "options": {}},
            ],
            "indexes": [
                "CREATE UNIQUE INDEX idx_gdrive_accounts_user_idx ON gdrive_accounts (user, account_index)"
            ],
            "listRule": None,
            "viewRule": None,
            "createRule": None,
            "updateRule": None,
            "deleteRule": None,
        }
        create_collection(client, pb_url, token, accounts_schema)
        accounts_id = get_collection_id(client, pb_url, token, "gdrive_accounts")

        # --- gdrive_files ---
        files_schema = {
            "name": "gdrive_files",
            "type": "base",
            "schema": [
                {
                    "name": "user",
                    "type": "relation",
                    "required": True,
                    "options": {
                        "collectionId": users_id,
                        "cascadeDelete": True,
                        "minSelect": None,
                        "maxSelect": 1,
                        "displayFields": [],
                    },
                },
                {
                    "name": "account",
                    "type": "relation",
                    "required": True,
                    "options": {
                        "collectionId": accounts_id,
                        "cascadeDelete": True,
                        "minSelect": None,
                        "maxSelect": 1,
                        "displayFields": [],
                    },
                },
                {"name": "file_name", "type": "text", "required": True, "options": {"min": None, "max": None, "pattern": ""}},
                {"name": "drive_file_id", "type": "text", "required": True, "options": {"min": None, "max": None, "pattern": ""}},
                {"name": "size", "type": "number", "required": False, "options": {"min": 0, "max": None, "noDecimal": True}},
                {"name": "mime_type", "type": "text", "required": False, "options": {"min": None, "max": None, "pattern": ""}},
                {"name": "thumbnail_link", "type": "text", "required": False, "options": {"min": None, "max": None, "pattern": ""}},
                {"name": "parent_drive_file_id", "type": "text", "required": False, "options": {"min": None, "max": None, "pattern": ""}},
                {"name": "drive_created_at", "type": "text", "required": False, "options": {"min": None, "max": None, "pattern": ""}},
            ],
            "indexes": [
                "CREATE UNIQUE INDEX idx_gdrive_files_drive_id ON gdrive_files (user, account, drive_file_id)"
            ],
            "listRule": None,
            "viewRule": None,
            "createRule": None,
            "updateRule": None,
            "deleteRule": None,
        }
        create_collection(client, pb_url, token, files_schema)
        files_id = get_collection_id(client, pb_url, token, "gdrive_files")

        # --- gdrive_folders ---
        folders_schema = {
            "name": "gdrive_folders",
            "type": "base",
            "schema": [
                {
                    "name": "user",
                    "type": "relation",
                    "required": True,
                    "options": {
                        "collectionId": users_id,
                        "cascadeDelete": True,
                        "minSelect": None,
                        "maxSelect": 1,
                        "displayFields": [],
                    },
                },
                {"name": "name", "type": "text", "required": True, "options": {"min": 1, "max": 200, "pattern": ""}},
            ],
            "indexes": [],
            "listRule": None,
            "viewRule": None,
            "createRule": None,
            "updateRule": None,
            "deleteRule": None,
        }
        create_collection(client, pb_url, token, folders_schema)
        folders_id = get_collection_id(client, pb_url, token, "gdrive_folders")

        # Add self-referential parent field to gdrive_folders
        r = client.get(f"{pb_url}/api/collections/gdrive_folders", headers=headers)
        folders_col = r.json()
        existing_field_names = [f["name"] for f in folders_col.get("schema", [])]
        if "parent" not in existing_field_names:
            folders_col.setdefault("schema", []).append({
                "name": "parent",
                "type": "relation",
                "required": False,
                "options": {
                    "collectionId": folders_id,
                    "cascadeDelete": False,
                    "minSelect": None,
                    "maxSelect": 1,
                    "displayFields": [],
                },
            })
            r2 = client.patch(f"{pb_url}/api/collections/gdrive_folders", headers=headers, json=folders_col)
            if r2.status_code in (200, 204):
                print("  ✓ Added 'parent' self-relation to gdrive_folders")
            else:
                print(f"  ! Could not add parent relation: {r2.status_code} {r2.text[:200]}")

        # --- gdrive_folder_files + gdrive_shares (depend on all above) ---
        for schema in build_schemas(users_id, accounts_id, files_id, folders_id):
            create_collection(client, pb_url, token, schema)

        # --- Create super admin user ---
        print("\n[3] Creating GDriveGenie super-admin user...")
        sa_email = ask("Super-admin email", "contactgenuinefind@gmail.com")
        sa_pass = ask_secret("Super-admin password")

        # Check if user already exists
        r = client.get(
            f"{pb_url}/api/collections/gdrive_users/records",
            headers=headers,
            params={"filter": f'email="{sa_email}"'},
        )
        existing_users = r.json().get("items", [])
        if existing_users:
            print(f"  ✓ User '{sa_email}' already exists — skipping")
        else:
            r = client.post(
                f"{pb_url}/api/collections/gdrive_users/records",
                headers=headers,
                json={
                    "email": sa_email,
                    "password": sa_pass,
                    "passwordConfirm": sa_pass,
                    "display_name": "Super Admin",
                    "is_super_admin": True,
                    "storage_limit_bytes": 16106127360,  # 15 GB
                    "storage_used_bytes": 0,
                    "emailVisibility": True,
                    "verified": True,
                },
            )
            if r.status_code in (200, 204):
                print(f"  ✓ Created super-admin user: {sa_email}")
            else:
                print(f"  ! Failed to create user: {r.status_code} {r.text[:300]}")

        # --- Generate secrets ---
        print("\n[4] Generating secrets...")
        jwt_secret = secrets.token_hex(32)
        encryption_key = Fernet.generate_key().decode()
        print(f"  ✓ JWT_SECRET generated")
        print(f"  ✓ ENCRYPTION_KEY generated")

    print("\n" + "=" * 60)
    print("SETUP COMPLETE — add these to your .env file:")
    print("=" * 60)
    print(f"PB_URL={pb_url}")
    print(f"PB_ADMIN_EMAIL={pb_admin_email}")
    print(f"PB_ADMIN_PASSWORD={pb_admin_password}")
    print(f"JWT_SECRET={jwt_secret}")
    print(f"ENCRYPTION_KEY={encryption_key}")
    print("=" * 60)
    print("\nDone! Restart your GDriveGenie backend after updating .env\n")


if __name__ == "__main__":
    main()
