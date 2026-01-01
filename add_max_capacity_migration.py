#!/usr/bin/env python3
"""
Migration script to add max_capacity column to Event table
"""
import sqlite3

def migrate():
    conn = sqlite3.connect('instance/friendship.db')
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(event)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'max_capacity' not in columns:
            print("Adding max_capacity column to event table...")
            cursor.execute('ALTER TABLE event ADD COLUMN max_capacity INTEGER')
            conn.commit()
            print("Successfully added max_capacity column")
        else:
            print("max_capacity column already exists, skipping migration")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
