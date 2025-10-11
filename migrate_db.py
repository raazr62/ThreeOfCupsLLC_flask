"""
Database migration script to add password reset fields to User table.
Run this script once to update the existing database schema.
"""
import sqlite3
import os

# Path to the database
db_path = 'instance/friendship.db'

def migrate_database():
    """Add reset_token and reset_token_expiry columns to User table if they don't exist"""

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("The database will be created when you first run the application.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(user)")
    columns = [column[1] for column in cursor.fetchall()]

    migrations_performed = []

    # Add reset_token column if it doesn't exist
    if 'reset_token' not in columns:
        cursor.execute('ALTER TABLE user ADD COLUMN reset_token VARCHAR(100)')
        migrations_performed.append('reset_token')
        print("✓ Added reset_token column")
    else:
        print("→ reset_token column already exists")

    # Add reset_token_expiry column if it doesn't exist
    if 'reset_token_expiry' not in columns:
        cursor.execute('ALTER TABLE user ADD COLUMN reset_token_expiry DATETIME')
        migrations_performed.append('reset_token_expiry')
        print("✓ Added reset_token_expiry column")
    else:
        print("→ reset_token_expiry column already exists")

    conn.commit()
    conn.close()

    if migrations_performed:
        print(f"\n✅ Migration completed successfully! Added {len(migrations_performed)} column(s).")
    else:
        print("\n✅ Database schema is up to date. No migrations needed.")

if __name__ == '__main__':
    print("Starting database migration...")
    print(f"Database path: {db_path}\n")
    migrate_database()
