"""
Database migration script to add email verification fields to the User model.

This script adds the following fields:
- email_verified (Boolean, default=False)
- verification_token (String, nullable=True)
- verification_token_expiry (DateTime, nullable=True)

Run this script ONCE after updating models.py to add the new fields.
Admin users will be automatically marked as verified.
"""

from app import app, db
from models import User
from sqlalchemy import inspect

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_database():
    """Add email verification columns to the User table"""
    with app.app_context():
        print("Starting database migration...")

        # Check if columns already exist
        if column_exists('user', 'email_verified'):
            print("✓ email_verified column already exists")
        else:
            print("Adding email_verified column...")
            db.engine.execute('ALTER TABLE user ADD COLUMN email_verified BOOLEAN DEFAULT 0')
            print("✓ email_verified column added")

        if column_exists('user', 'verification_token'):
            print("✓ verification_token column already exists")
        else:
            print("Adding verification_token column...")
            db.engine.execute('ALTER TABLE user ADD COLUMN verification_token VARCHAR(100)')
            print("✓ verification_token column added")

        if column_exists('user', 'verification_token_expiry'):
            print("✓ verification_token_expiry column already exists")
        else:
            print("Adding verification_token_expiry column...")
            db.engine.execute('ALTER TABLE user ADD COLUMN verification_token_expiry DATETIME')
            print("✓ verification_token_expiry column added")

        # Mark all admin users as verified
        print("\nMarking admin users as verified...")
        admin_users = User.query.filter_by(is_admin=True).all()
        for admin in admin_users:
            admin.email_verified = True

        if admin_users:
            db.session.commit()
            print(f"✓ Marked {len(admin_users)} admin user(s) as verified")
        else:
            print("✓ No admin users found")

        print("\n✅ Migration completed successfully!")
        print("\nNote: All existing non-admin users will need to verify their email addresses.")
        print("Admin users have been automatically marked as verified.")

if __name__ == '__main__':
    try:
        migrate_database()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nIf you're using SQLAlchemy migrations (Alembic/Flask-Migrate),")
        print("you may need to use that instead of this script.")
