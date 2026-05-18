#!/usr/bin/env python3
"""Migration: bring the legacy `user` table up to the current models.User schema.

This repo does not use Alembic/Flask-Migrate. Some older databases may have a
very small `user` table (e.g. only id/username/password_hash/is_admin).

This script is safe to run multiple times. It:
- Adds missing columns via ALTER TABLE
- Backfills minimal placeholders for existing rows (so the app can render)

Usage:
  python migrate_user_table.py
"""

from __future__ import annotations

import os
import sqlite3


DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "friendship.db")


EXPECTED_COLUMNS: list[tuple[str, str]] = [
    ("first_name", "VARCHAR(100)"),
    ("last_name", "VARCHAR(100)"),
    ("email", "VARCHAR(150)"),
    ("bio", "TEXT"),
    ("profile_picture", "VARCHAR(200)"),
    ("reset_token", "VARCHAR(100)"),
    ("reset_token_expiry", "DATETIME"),
    ("pronouns", "VARCHAR(100)"),
    ("date_of_birth", "DATE"),
    ("location", "VARCHAR(200)"),
    ("email_verified", "BOOLEAN DEFAULT 0"),
    ("verification_token", "VARCHAR(100)"),
    ("verification_token_expiry", "DATETIME"),
    ("pending_email", "VARCHAR(150)"),
    ("email_change_token", "VARCHAR(100)"),
    ("email_change_token_expiry", "DATETIME"),
    ("can_retake_assessment", "BOOLEAN DEFAULT 0"),
    ("has_paid", "BOOLEAN DEFAULT 0"),
    ("payment_waived_at", "DATETIME"),
    ("profile_incomplete", "BOOLEAN DEFAULT 0"),
    ("profile_completion_token", "VARCHAR(100)"),
    ("profile_completion_token_expiry", "DATETIME"),
    ("disclaimer_agreed", "BOOLEAN DEFAULT 0"),
    ("disclaimer_agreed_at", "DATETIME"),
]


def _table_exists(cur: sqlite3.Cursor, table: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None


def migrate_user_table(db_path: str = DB_PATH) -> None:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        if not _table_exists(cur, "user"):
            # If the user table doesn't exist, the app's db.create_all() will create it.
            print("Table 'user' does not exist; nothing to migrate.")
            return

        cur.execute("PRAGMA table_info(user)")
        existing_cols = {row[1] for row in cur.fetchall()}

        added = []
        for col_name, col_def in EXPECTED_COLUMNS:
            if col_name not in existing_cols:
                cur.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_def}")
                added.append(col_name)

        if added:
            print(f"✓ Added columns to user: {', '.join(added)}")
        else:
            print("✓ User table already has all expected columns")

        # Backfill placeholders for legacy rows so the app can safely render names/emails.
        # Use id-based placeholders to avoid accidental duplicates.
        # Note: SQLite uses || for string concat.
        cur.execute("UPDATE user SET first_name = COALESCE(first_name, username, 'User')")
        cur.execute("UPDATE user SET last_name = COALESCE(last_name, '')")
        cur.execute("UPDATE user SET email = COALESCE(email, 'user' || id || '@example.com')")

        conn.commit()
        print("✓ Backfilled placeholders for existing users")

    finally:
        conn.close()


def main() -> int:
    migrate_user_table()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
