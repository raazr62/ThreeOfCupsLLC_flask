"""Migration: add event matchmaking whiteboard tables and is_matchmaking flag."""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'friendship.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add is_matchmaking to event table
try:
    cursor.execute("ALTER TABLE event ADD COLUMN is_matchmaking BOOLEAN NOT NULL DEFAULT 0")
    print("Added is_matchmaking to event table")
except sqlite3.OperationalError as e:
    print(f"Skipping (likely already exists): {e}")

# Create event_matchmaking_draft table
cursor.execute("""
CREATE TABLE IF NOT EXISTS event_matchmaking_draft (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL REFERENCES event(id),
    user1_id INTEGER NOT NULL REFERENCES user(id),
    user2_id INTEGER NOT NULL REFERENCES user(id),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
print("Created event_matchmaking_draft table")

# Create event_user_board_position table
cursor.execute("""
CREATE TABLE IF NOT EXISTS event_user_board_position (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL REFERENCES event(id),
    user_id INTEGER NOT NULL REFERENCES user(id),
    pos_x REAL DEFAULT 100.0,
    pos_y REAL DEFAULT 100.0,
    UNIQUE (event_id, user_id)
)
""")
print("Created event_user_board_position table")

conn.commit()
conn.close()
print("Migration complete!")
