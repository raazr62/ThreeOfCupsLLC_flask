"""Migration: add card1_id and card2_id to event_matchmaking_draft."""
import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'friendship.db')
conn = sqlite3.connect(db_path)
cur  = conn.cursor()

for col in ('card1_id', 'card2_id'):
    try:
        cur.execute(f"ALTER TABLE event_matchmaking_draft ADD COLUMN {col} INTEGER REFERENCES event_board_card(id)")
        print(f"Added column {col}")
    except Exception as e:
        print(f"Skipped {col}: {e}")

conn.commit()
conn.close()
print("Migration complete!")
