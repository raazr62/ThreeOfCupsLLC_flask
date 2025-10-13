"""
Migration script to create the ReviewerAssessment table using Flask app context.

This script uses your existing Flask app configuration and can be run safely
multiple times - it will only create the table if it doesn't exist.

Usage:
    python3 migrate_reviewer_assessment_flask.py
"""

from app import app, db
from models import ReviewerAssessment
from sqlalchemy import inspect

def table_exists(table_name):
    """Check if a table exists in the database."""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

def verify_table_structure():
    """Verify that the table has all required columns."""
    inspector = inspect(db.engine)
    if not table_exists('reviewer_assessment'):
        return False

    columns = inspector.get_columns('reviewer_assessment')
    column_names = [col['name'] for col in columns]

    required_columns = ['id', 'name', 'pronouns', 'age_range', 'location', 'answers',
                       'created_at', 'reviewed', 'admin_notes']

    missing_columns = [col for col in required_columns if col not in column_names]

    if missing_columns:
        print(f"⚠ Warning: Missing columns: {', '.join(missing_columns)}")
        return False

    print("✓ All required columns are present")
    return True

def main():
    """Run the migration."""
    print("=" * 60)
    print("Three of Cups - ReviewerAssessment Table Migration")
    print("=" * 60)
    print()

    with app.app_context():
        try:
            # Check if table exists
            if table_exists('reviewer_assessment'):
                print("⚠ Table 'reviewer_assessment' already exists")
                print()
                print("Verifying table structure...")
                if verify_table_structure():
                    print()
                    print("=" * 60)
                    print("Table structure verified - no migration needed!")
                    print("=" * 60)
                else:
                    print()
                    print("=" * 60)
                    print("⚠ Table structure needs updates")
                    print("=" * 60)
                    print()
                    print("Please run the following to update:")
                    print("  db.create_all()")
                    print()
                    print("Or drop and recreate the table:")
                    print("  db.drop_all()")
                    print("  db.create_all()")
            else:
                print("Creating 'reviewer_assessment' table...")
                db.create_all()
                print("✓ reviewer_assessment table created successfully")
                print()
                print("Verifying table structure...")
                verify_table_structure()
                print()
                print("=" * 60)
                print("Migration completed successfully!")
                print("=" * 60)

        except Exception as e:
            print()
            print("=" * 60)
            print("⚠ ERROR: Migration failed!")
            print("=" * 60)
            print(f"Error details: {str(e)}")
            print()
            print("Please check your database configuration and try again.")
            return 1

    return 0

if __name__ == '__main__':
    exit(main())
