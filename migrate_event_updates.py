"""
Migration: Add new Event fields and EventEnergyExchange table.

New Event fields:
  - address (TEXT, nullable) - street address
  - end_time (DATETIME, nullable) - optional end time
  - price_max (FLOAT, nullable) - upper bound for price range

New table:
  - event_energy_exchange
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'friendship.db')


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Event table additions ---
    existing_columns = {row[1] for row in cursor.execute("PRAGMA table_info(event)")}

    if 'address' not in existing_columns:
        cursor.execute("ALTER TABLE event ADD COLUMN address TEXT")
        print("Added 'address' column to event table.")
    else:
        print("'address' column already exists.")

    if 'end_time' not in existing_columns:
        cursor.execute("ALTER TABLE event ADD COLUMN end_time DATETIME")
        print("Added 'end_time' column to event table.")
    else:
        print("'end_time' column already exists.")

    if 'price_max' not in existing_columns:
        cursor.execute("ALTER TABLE event ADD COLUMN price_max FLOAT")
        print("Added 'price_max' column to event table.")
    else:
        print("'price_max' column already exists.")

    # --- EventEnergyExchange table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_energy_exchange (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL REFERENCES event(id),
            user_id INTEGER NOT NULL REFERENCES user(id),
            indicated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            confirmed BOOLEAN DEFAULT 0,
            amount_confirmed FLOAT,
            admin_notes VARCHAR(500)
        )
    """)
    print("Created (or verified) event_energy_exchange table.")

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == '__main__':
    migrate()
