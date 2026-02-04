"""
Migration script to add disclaimer_agreed and disclaimer_agreed_at fields to User table.
This tracks whether users have agreed to the service disclaimer.
"""
from app import app, db
from models import User

def migrate():
    with app.app_context():
        # Check if columns already exist
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]

        if 'disclaimer_agreed' not in columns:
            print("Adding disclaimer_agreed column to User table...")
            with db.engine.connect() as conn:
                conn.execute(db.text(
                    'ALTER TABLE user ADD COLUMN disclaimer_agreed BOOLEAN DEFAULT 0'
                ))
                conn.commit()
            print("  Column 'disclaimer_agreed' added successfully!")
        else:
            print("Column 'disclaimer_agreed' already exists. Skipping.")

        if 'disclaimer_agreed_at' not in columns:
            print("Adding disclaimer_agreed_at column to User table...")
            with db.engine.connect() as conn:
                conn.execute(db.text(
                    'ALTER TABLE user ADD COLUMN disclaimer_agreed_at DATETIME'
                ))
                conn.commit()
            print("  Column 'disclaimer_agreed_at' added successfully!")
        else:
            print("Column 'disclaimer_agreed_at' already exists. Skipping.")

        print("\nMigration complete!")

if __name__ == '__main__':
    migrate()
