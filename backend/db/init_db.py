"""
Database initialization script for MySQL setup with SQLAlchemy.
Run this script to create all necessary tables in the database.
"""

from db import init_db, engine

if __name__ == "__main__":
    try:
        # Create all tables
        init_db()
        print("✓ Database initialized successfully!")
        print(f"✓ Connected to: {engine.url}")
        print("✓ Tables created: courses, sections, files")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        raise
