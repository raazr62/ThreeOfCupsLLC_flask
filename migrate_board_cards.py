"""Migration: add event_board_card table; migrate existing position data into it."""
import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'friendship.db')
conn   = sqlite3.connect(db_path)
cur    = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS event_board_card (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id   INTEGER NOT NULL REFERENCES event(id),
    user_id    INTEGER NOT NULL REFERENCES user(id),
    pos_x      REAL    DEFAULT 100.0,
    pos_y      REAL    DEFAULT 100.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
print("Created event_board_card table")

# Migrate any rows already in event_user_board_position
cur.execute("SELECT COUNT(*) FROM event_user_board_position")
count = cur.fetchone()[0]
if count:
    cur.execute("""
        INSERT OR IGNORE INTO event_board_card (event_id, user_id, pos_x, pos_y)
        SELECT event_id, user_id, pos_x, pos_y FROM event_user_board_position
    """)
    print(f"Migrated {count} position(s) from event_user_board_position")

conn.commit()
conn.close()
print("Migration complete!")
