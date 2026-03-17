from services.d1_client import D1Client, get_d1  # noqa: F401 — re-exported for routes

CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS drive_accounts (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        account_index INTEGER NOT NULL UNIQUE,
        email         TEXT,
        refresh_token TEXT,
        access_token  TEXT,
        token_expiry  TEXT,
        is_connected  INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS files (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name             TEXT NOT NULL,
        drive_file_id         TEXT NOT NULL,
        account_index         INTEGER NOT NULL,
        size                  INTEGER DEFAULT 0,
        mime_type             TEXT,
        thumbnail_link        TEXT,
        parent_drive_file_id  TEXT,
        created_at            TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS profile (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        display_name         TEXT,
        bio                  TEXT,
        avatar_drive_file_id TEXT,
        avatar_account_index INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS app_config (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
]

# Idempotent migrations — errors are swallowed in main.py if column already exists
MIGRATION_SQL = [
    "ALTER TABLE files ADD COLUMN parent_drive_file_id TEXT",
]
