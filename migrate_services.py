"""
Migration: create the service table.
Run with: python3 migrate_services.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'friendship.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service'")
    if cur.fetchone():
        print('service table already exists — skipping.')
        conn.close()
        return

    cur.execute("""
        CREATE TABLE service (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) NOT NULL,
            price_display VARCHAR(200),
            description TEXT,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print('Created service table.')
    conn.close()

if __name__ == '__main__':
    migrate()
