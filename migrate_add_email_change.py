"""
Database migration script to add email change verification fields to the User model.

This script adds the following fields:
- pending_email (String, nullable=True)
- email_change_token (String, nullable=True)
- email_change_token_expiry (DateTime, nullable=True)

Run this script ONCE after updating models.py to add the new fields.
"""

from app import app, db
from sqlalchemy import inspect, text

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_database():
    """Add email change verification columns to the User table"""
    with app.app_context():
        print("Starting database migration for email change functionality...")

        # Check if columns already exist
        if column_exists('user', 'pending_email'):
            print("✓ pending_email column already exists")
        else:
            print("Adding pending_email column...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE user ADD COLUMN pending_email VARCHAR(150)'))
                conn.commit()
            print("✓ pending_email column added")

        if column_exists('user', 'email_change_token'):
            print("✓ email_change_token column already exists")
        else:
            print("Adding email_change_token column...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE user ADD COLUMN email_change_token VARCHAR(100)'))
                conn.commit()
            print("✓ email_change_token column added")

        if column_exists('user', 'email_change_token_expiry'):
            print("✓ email_change_token_expiry column already exists")
        else:
            print("Adding email_change_token_expiry column...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE user ADD COLUMN email_change_token_expiry DATETIME'))
                conn.commit()
            print("✓ email_change_token_expiry column added")

        print("\n✅ Migration completed successfully!")
        print("\nEmail change verification is now enabled.")
        print("When users change their email on the dashboard:")
        print("  1. A notification will be sent to their old email")
        print("  2. A verification link will be sent to the new email")
        print("  3. Email will only update after the new address is verified")

if __name__ == '__main__':
    try:
        migrate_database()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nIf you're using SQLAlchemy migrations (Alembic/Flask-Migrate),")
        print("you may need to use that instead of this script.")
