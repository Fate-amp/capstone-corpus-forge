"""
Database utilities module.

Provides database session management and helper functions.

TODO: Add connection pooling configuration
TODO: Add query logging for debugging
TODO: Add transaction management utilities
"""

from models import db
import logging

logger = logging.getLogger(__name__)


def init_db(app):
    """
    Initialize database with Flask app.
    
    Args:
        app: Flask application instance
        
    TODO: Add migration support (Alembic)
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")


def get_or_create(model, **kwargs):
    """
    Get or create a database record.
    
    Args:
        model: SQLAlchemy model class
        **kwargs: Filter criteria
        
    Returns:
        Tuple[object, bool]: (model_instance, created_flag)
        
    TODO: Add error handling
    """
    instance = db.session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance, True


def safe_commit():
    """
    Safely commit database transaction with error handling.
    
    TODO: Add logging
    TODO: Add retry logic
    """
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database commit error: {str(e)}")
        raise
