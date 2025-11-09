#!/usr/bin/env python3
"""
Script to delete specific users and all their associated data.
Deletes: User account, Assessments, and Matches
"""

import sys
from app import app
from models import db, User, Assessment, Match


def delete_user(identifier):
    """
    Delete a user and all associated data by username or email.

    Args:
        identifier: Username or email of the user to delete

    Returns:
        True if successful, False otherwise
    """
    with app.app_context():
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if not user:
            print(f"❌ User not found: {identifier}")
            return False

        # Collect information about what will be deleted
        assessments = Assessment.query.filter_by(user_id=user.id).all()
        matches = Match.query.filter(
            (Match.user1_id == user.id) | (Match.user2_id == user.id)
        ).all()

        print(f"\n{'='*60}")
        print(f"Found user: {user.username} ({user.email})")
        print(f"ID: {user.id}")
        print(f"Name: {user.first_name} {user.last_name}")
        print(f"{'='*60}")
        print(f"Associated data to be deleted:")
        print(f"  - Assessments: {len(assessments)}")
        print(f"  - Matches: {len(matches)}")
        print(f"{'='*60}\n")

        # Confirm deletion
        response = input(f"Are you sure you want to delete this user? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Deletion cancelled.")
            return False

        try:
            # Delete matches first (foreign key constraints)
            for match in matches:
                db.session.delete(match)
            print(f"✓ Deleted {len(matches)} match(es)")

            # Delete assessments
            for assessment in assessments:
                db.session.delete(assessment)
            print(f"✓ Deleted {len(assessments)} assessment(s)")

            # Delete user
            db.session.delete(user)
            db.session.commit()
            print(f"✓ Deleted user: {user.username}")

            print(f"\n✅ Successfully deleted user and all associated data!")
            return True

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during deletion: {str(e)}")
            return False


def list_all_users():
    """List all users in the system."""
    with app.app_context():
        users = User.query.order_by(User.username).all()

        if not users:
            print("No users found in the system.")
            return

        print(f"\n{'='*80}")
        print(f"{'ID':<6} {'Username':<20} {'Email':<30} {'Name':<20}")
        print(f"{'='*80}")

        for user in users:
            name = f"{user.first_name} {user.last_name}"
            print(f"{user.id:<6} {user.username:<20} {user.email:<30} {name:<20}")

        print(f"{'='*80}")
        print(f"Total users: {len(users)}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python delete_users.py <username_or_email>  - Delete a specific user")
        print("  python delete_users.py --list               - List all users")
        print("\nExamples:")
        print("  python delete_users.py john_doe")
        print("  python delete_users.py john@example.com")
        sys.exit(1)

    if sys.argv[1] == '--list':
        list_all_users()
    else:
        identifier = sys.argv[1]
        delete_user(identifier)


if __name__ == '__main__':
    main()
