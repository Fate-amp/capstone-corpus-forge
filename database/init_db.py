"""
Database initialization module.

Creates database tables and initializes ChromaDB collections.
Run this on first app startup.

Usage:
    python database/init_db.py

TODO: Add database migration support (Alembic)
TODO: Add seed data for development
TODO: Add backup/restore utilities
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from models import Document, ChatMessage, UsageLog, Settings


def init_database():
    """
    Initialize database by creating all tables.
    
    TODO: Add transaction handling for safety
    TODO: Add logging
    TODO: Add check to prevent re-initialization
    """
    print("Initializing database...")
    
    with app.app_context():
        # Drop all existing tables and recreate (development only)
        # WARNING: This will delete all data! In production, use Alembic migrations.
        db.drop_all()
        print("✓ Dropped existing tables")
        
        # Create all tables
        db.create_all()
        print("✓ Database tables created with new schema (includes full_content column)")
        
        # Initialize default settings (if not exists)
        if Settings.query.first() is None:
            default_settings = Settings()
            db.session.add(default_settings)
            db.session.commit()
            print("✓ Default settings created")
        
        # Create uploads directory if it doesn't exist
        uploads_dir = Path(app.config['UPLOAD_FOLDER'])
        uploads_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Uploads directory ready: {uploads_dir}")
        
        # Initialize ChromaDB
        # TODO: Move this to a separate services/chromadb_service.py
        chromadb_path = app.config.get('CHROMADB_PATH', './.chromadb')
        chromadb_dir = Path(chromadb_path)
        chromadb_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ ChromaDB directory ready: {chromadb_dir}")
        
        print("\n✓ Database initialization complete!")


if __name__ == '__main__':
    app = create_app()
    init_database()
