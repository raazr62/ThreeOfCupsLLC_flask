"""
Migration script to add can_retake_assessment field to User table
This allows admins to enable assessment retakes for specific users in the future.
"""
from app import app, db
from models import User

def migrate():
    with app.app_context():
        # Check if column already exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]

        if 'can_retake_assessment' not in columns:
            print("Adding can_retake_assessment column to User table...")
            with db.engine.connect() as conn:
                conn.execute(db.text(
                    'ALTER TABLE user ADD COLUMN can_retake_assessment BOOLEAN DEFAULT 0'
                ))
                conn.commit()
            print("✓ Column added successfully!")
        else:
            print("Column 'can_retake_assessment' already exists. Skipping migration.")

if __name__ == '__main__':
    migrate()
