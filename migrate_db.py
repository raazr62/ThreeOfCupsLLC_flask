"""
Database migration script to add new columns to the User table.
This script adds pronouns, date_of_birth, and location columns.
"""
import sqlite3
import os

def migrate_database():
    db_path = 'instance/friendship.db'

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]

        # Add pronouns column if it doesn't exist
        if 'pronouns' not in columns:
            print("Adding 'pronouns' column...")
            cursor.execute("ALTER TABLE user ADD COLUMN pronouns VARCHAR(100)")
            print("✓ Added 'pronouns' column")
        else:
            print("'pronouns' column already exists")

        # Add date_of_birth column if it doesn't exist
        if 'date_of_birth' not in columns:
            print("Adding 'date_of_birth' column...")
            cursor.execute("ALTER TABLE user ADD COLUMN date_of_birth DATE")
            print("✓ Added 'date_of_birth' column")
        else:
            print("'date_of_birth' column already exists")

        # Add location column if it doesn't exist
        if 'location' not in columns:
            print("Adding 'location' column...")
            cursor.execute("ALTER TABLE user ADD COLUMN location VARCHAR(200)")
            print("✓ Added 'location' column")
        else:
            print("'location' column already exists")

        conn.commit()
        print("\nMigration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
