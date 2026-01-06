"""
Migration script to add payment tracking fields to User table
- has_paid: Boolean flag to track if user has paid for match service
- payment_waived_at: Timestamp when admin waived payment (for audit trail)
"""
from app import app, db
from models import User
from datetime import datetime

def migrate():
    with app.app_context():
        # Check if columns already exist
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]

        # Add has_paid column
        if 'has_paid' not in columns:
            print("Adding has_paid column to User table...")
            with db.engine.connect() as conn:
                conn.execute(db.text(
                    'ALTER TABLE user ADD COLUMN has_paid BOOLEAN DEFAULT 0'
                ))
                conn.commit()
            print("✓ has_paid column added successfully!")
        else:
            print("Column 'has_paid' already exists. Skipping.")

        # Add payment_waived_at column
        if 'payment_waived_at' not in columns:
            print("Adding payment_waived_at column to User table...")
            with db.engine.connect() as conn:
                conn.execute(db.text(
                    'ALTER TABLE user ADD COLUMN payment_waived_at DATETIME'
                ))
                conn.commit()
            print("✓ payment_waived_at column added successfully!")
        else:
            print("Column 'payment_waived_at' already exists. Skipping.")

        # Mark all admin users as having paid (admins don't pay for matches)
        print("Marking all admin users as paid...")
        admin_users = User.query.filter_by(is_admin=True).all()
        for admin in admin_users:
            admin.has_paid = True
        db.session.commit()
        print(f"✓ Marked {len(admin_users)} admin user(s) as paid")

        print("\n✅ Migration completed successfully!")

if __name__ == '__main__':
    migrate()
