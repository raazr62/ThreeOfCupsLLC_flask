"""
Migration script to add email content columns to Match table
This allows storing the personalized HTML email content sent to each user
when a match is finalized, enabling users to view match reasoning in a modal.
"""
from app import app, db

def migrate():
    with app.app_context():
        inspector = db.inspect(db.engine)

        # Get existing columns in match table
        columns = [col['name'] for col in inspector.get_columns('match')]

        # Add user1_email_content column if it doesn't exist
        if 'user1_email_content' not in columns:
            print("Adding user1_email_content column to match table...")
            with db.engine.connect() as conn:
                conn.execute(db.text('''
                    ALTER TABLE match ADD COLUMN user1_email_content TEXT
                '''))
                conn.commit()
            print("✓ user1_email_content column added successfully!")
        else:
            print("Column 'user1_email_content' already exists. Skipping.")

        # Add user2_email_content column if it doesn't exist
        if 'user2_email_content' not in columns:
            print("Adding user2_email_content column to match table...")
            with db.engine.connect() as conn:
                conn.execute(db.text('''
                    ALTER TABLE match ADD COLUMN user2_email_content TEXT
                '''))
                conn.commit()
            print("✓ user2_email_content column added successfully!")
        else:
            print("Column 'user2_email_content' already exists. Skipping.")

if __name__ == '__main__':
    migrate()
