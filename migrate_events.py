#!/usr/bin/env python3
"""
Migration script to add Event and EventRSVP tables to the database.
Run this script to update your database with the new events feature.
"""

from app import app, db
from models import Event, EventRSVP

def migrate_database():
    """Create Event and EventRSVP tables if they don't exist."""
    with app.app_context():
        # Create tables
        db.create_all()
        print("✓ Database migration completed successfully!")
        print("✓ Event and EventRSVP tables have been created.")
        print("\nYou can now:")
        print("1. Visit /admin/events as an admin to create events")
        print("2. Visit /events to view upcoming events")
        print("3. Users can RSVP to events when logged in")

if __name__ == '__main__':
    migrate_database()
