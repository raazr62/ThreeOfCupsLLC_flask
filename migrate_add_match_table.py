"""
Migration script to add Match table for managing pending and finalized matches
This allows admins to create pending matches, add notes, draft emails, and finalize matches.
"""
from app import app, db
from models import Match

def migrate():
    with app.app_context():
        # Check if match table already exists
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()

        if 'match' not in tables:
            print("Creating Match table...")
            with db.engine.connect() as conn:
                conn.execute(db.text('''
                    CREATE TABLE match (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user1_id INTEGER NOT NULL,
                        user2_id INTEGER NOT NULL,
                        assessment1_id INTEGER NOT NULL,
                        assessment2_id INTEGER NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        admin_notes TEXT,
                        draft_email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        finalized_at TIMESTAMP,
                        FOREIGN KEY (user1_id) REFERENCES user(id),
                        FOREIGN KEY (user2_id) REFERENCES user(id),
                        FOREIGN KEY (assessment1_id) REFERENCES assessment(id),
                        FOREIGN KEY (assessment2_id) REFERENCES assessment(id)
                    )
                '''))
                conn.commit()
            print("✓ Match table created successfully!")
        else:
            print("Table 'match' already exists. Skipping migration.")

if __name__ == '__main__':
    migrate()
