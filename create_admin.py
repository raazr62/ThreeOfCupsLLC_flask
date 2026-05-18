from app import app, db
from models import User
from migrate_user_table import migrate_user_table

def create_admin_user():
    # Ensure legacy databases have the columns expected by models.User.
    # Without this, any ORM query can fail with "no such column".
    migrate_user_table()

    with app.app_context():
        # Create all database tables if they don't exist
        db.create_all()

        # Check if admin user already exists
        existing_admin = User.query.filter_by(username='admin').first()
        if existing_admin:
            print(f"User 'admin' already exists (ID: {existing_admin.id})")
            return

        # Create admin user
        # Note: Password "admin" doesn't meet validation requirements
        # Using "Admin123!" instead which meets all requirements:
        # - At least 8 characters
        # - Contains uppercase letter
        # - Contains lowercase letter
        # - Contains number
        # - Contains special character
        admin = User(
            username='admin',
            first_name='Admin',
            last_name='User',
            email='admin@threeofcups.com',
            is_admin=True
        )
        admin.set_password('Admin123!')  # Secure password that meets validation

        db.session.add(admin)
        db.session.commit()

        print("Admin user created successfully!")
        print(f"Username: admin")
        print(f"Password: Admin123!")
        print(f"Email: admin@threeofcups.com")

if __name__ == '__main__':
    create_admin_user()
