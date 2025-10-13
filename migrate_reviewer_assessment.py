"""
Migration script to create the ReviewerAssessment table on Amazon Lightsail instance.

This script can be run safely multiple times - it will only create the table if it doesn't exist.

Usage:
    python3 migrate_reviewer_assessment.py
"""

import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Database connection configuration
# Update these values to match your Lightsail instance configuration
DATABASE_CONFIG = {
    'host': 'localhost',  # or your database host
    'database': 'three_of_cups',  # your database name
    'user': 'your_db_user',  # your database user
    'password': 'your_db_password'  # your database password
}

def get_database_url():
    """Construct the database URL from config."""
    return f"mysql+pymysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}/{DATABASE_CONFIG['database']}"

def table_exists(engine, table_name):
    """Check if a table exists in the database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def create_reviewer_assessment_table(engine):
    """Create the reviewer_assessment table."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS reviewer_assessment (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(200) NOT NULL,
        pronouns VARCHAR(100),
        age_range VARCHAR(50),
        location VARCHAR(200),
        answers TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        reviewed BOOLEAN DEFAULT FALSE,
        admin_notes TEXT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()

    print("✓ reviewer_assessment table created successfully")

def verify_table_structure(engine):
    """Verify that the table has all required columns."""
    inspector = inspect(engine)
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

def add_missing_columns(engine):
    """Add any missing columns to the reviewer_assessment table."""
    inspector = inspect(engine)
    columns = inspector.get_columns('reviewer_assessment')
    column_names = [col['name'] for col in columns]

    column_definitions = {
        'pronouns': 'VARCHAR(100)',
        'age_range': 'VARCHAR(50)',
        'location': 'VARCHAR(200)',
        'reviewed': 'BOOLEAN DEFAULT FALSE',
        'admin_notes': 'TEXT'
    }

    with engine.connect() as conn:
        for col_name, col_def in column_definitions.items():
            if col_name not in column_names:
                alter_sql = f"ALTER TABLE reviewer_assessment ADD COLUMN {col_name} {col_def};"
                try:
                    conn.execute(text(alter_sql))
                    conn.commit()
                    print(f"✓ Added column: {col_name}")
                except SQLAlchemyError as e:
                    print(f"⚠ Warning: Could not add column {col_name}: {str(e)}")

def main():
    """Run the migration."""
    print("=" * 60)
    print("Three of Cups - ReviewerAssessment Table Migration")
    print("=" * 60)
    print()

    # Check if configuration needs to be updated
    if DATABASE_CONFIG['user'] == 'your_db_user':
        print("⚠ ERROR: Please update the DATABASE_CONFIG in this script")
        print("   with your actual database credentials before running.")
        print()
        print("   Edit the following variables at the top of this file:")
        print("   - host")
        print("   - database")
        print("   - user")
        print("   - password")
        sys.exit(1)

    try:
        # Create database engine
        database_url = get_database_url()
        print(f"Connecting to database: {DATABASE_CONFIG['database']}@{DATABASE_CONFIG['host']}")
        engine = create_engine(database_url)

        # Test connection
        with engine.connect() as conn:
            print("✓ Database connection successful")

        print()

        # Check if table exists
        if table_exists(engine, 'reviewer_assessment'):
            print("⚠ Table 'reviewer_assessment' already exists")
            print("  Checking for missing columns...")
            add_missing_columns(engine)
        else:
            print("Creating 'reviewer_assessment' table...")
            create_reviewer_assessment_table(engine)

        print()

        # Verify table structure
        print("Verifying table structure...")
        verify_table_structure(engine)

        print()
        print("=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)

    except SQLAlchemyError as e:
        print()
        print("=" * 60)
        print("⚠ ERROR: Migration failed!")
        print("=" * 60)
        print(f"Error details: {str(e)}")
        print()
        print("Please check your database configuration and try again.")
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 60)
        print("⚠ ERROR: Unexpected error occurred!")
        print("=" * 60)
        print(f"Error details: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
