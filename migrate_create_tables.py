#!/usr/bin/env python3
"""Create any missing tables defined in models.py.

This project uses Flask-SQLAlchemy without Alembic/Flask-Migrate.
So to create NEW tables you:
  1) add a new db.Model class in models.py
  2) run this script (it calls db.create_all())

Important: db.create_all() does NOT add columns to existing tables.
For existing tables, use a dedicated migration script with ALTER TABLE.

Usage:
  python migrate_create_tables.py
"""

from sqlalchemy import inspect

from app import app, db


def main() -> int:
    with app.app_context():
        print(f"DB: {db.engine.url}")
        db.create_all()

        inspector = inspect(db.engine)
        tables = sorted(inspector.get_table_names())

        print("✓ create_all complete")
        print(f"✓ tables ({len(tables)}):")
        for name in tables:
            print(f"  - {name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
