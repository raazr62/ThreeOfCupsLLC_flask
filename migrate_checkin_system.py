"""
Database migration script for Event Check-In System
Run this script to add the new tables and columns needed for the check-in feature.

Usage:
    python migrate_checkin_system.py
"""

from app import app, db
from sqlalchemy import text

def migrate_database():
    """Add new tables and columns for the check-in system"""
    print("Starting database migration for Event Check-In System...")

    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        try:
            # Add new columns to User table
            print("Adding columns to User table...")
            try:
                connection.execute(text("ALTER TABLE user ADD COLUMN profile_incomplete BOOLEAN DEFAULT 0"))
                print("  ✓ Added profile_incomplete column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("  - profile_incomplete column already exists")
                else:
                    raise

            try:
                connection.execute(text("ALTER TABLE user ADD COLUMN profile_completion_token VARCHAR(100)"))
                print("  ✓ Added profile_completion_token column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("  - profile_completion_token column already exists")
                else:
                    raise

            try:
                connection.execute(text("ALTER TABLE user ADD COLUMN profile_completion_token_expiry DATETIME"))
                print("  ✓ Added profile_completion_token_expiry column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("  - profile_completion_token_expiry column already exists")
                else:
                    raise

            # Add new columns to Event table
            print("\nAdding columns to Event table...")
            try:
                connection.execute(text("ALTER TABLE event ADD COLUMN kiosk_token VARCHAR(100)"))
                print("  ✓ Added kiosk_token column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("  - kiosk_token column already exists")
                else:
                    raise

            try:
                connection.execute(text("ALTER TABLE event ADD COLUMN kiosk_token_expiry DATETIME"))
                print("  ✓ Added kiosk_token_expiry column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("  - kiosk_token_expiry column already exists")
                else:
                    raise

            # Create EventCheckIn table
            print("\nCreating EventCheckIn table...")
            try:
                connection.execute(text("""
                    CREATE TABLE event_check_in (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        checked_in_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        had_rsvp BOOLEAN DEFAULT 0,
                        is_walk_in BOOLEAN DEFAULT 0,
                        FOREIGN KEY (event_id) REFERENCES event (id),
                        FOREIGN KEY (user_id) REFERENCES user (id),
                        UNIQUE (event_id, user_id)
                    )
                """))
                print("  ✓ Created event_check_in table")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("  - event_check_in table already exists")
                else:
                    raise

            transaction.commit()
            print("\n✓ Database migration completed successfully!")
            print("\nNew features added:")
            print("  - EventCheckIn table for tracking check-ins")
            print("  - User.profile_incomplete field")
            print("  - User.profile_completion_token field")
            print("  - User.profile_completion_token_expiry field")
            print("  - Event.kiosk_token field")
            print("  - Event.kiosk_token_expiry field")
            print("\nThe event check-in system is now ready to use!")
            print("\nNext steps:")
            print("  1. Restart your Flask app")
            print("  2. Go to Admin Events page")
            print("  3. Click 'Generate Kiosk Link' for any event")
            print("  4. Open the kiosk link on a tablet/laptop at your event")
            print("  5. Attendees can now check themselves in!")

        except Exception as e:
            transaction.rollback()
            print(f"\n✗ Migration failed: {e}")
            raise
        finally:
            connection.close()

if __name__ == '__main__':
    try:
        migrate_database()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import sys
        sys.exit(1)
