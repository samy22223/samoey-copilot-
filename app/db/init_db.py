import logging
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.core.security import get_password_hash
from backend.models.user import User
from backend.db.session import engine, init_db as create_tables, get_db
from config.settings import settings

logger = logging.getLogger(__name__)

async def init_db(db: Session) -> None:
    """Initialize the database with default data."""
    try:
        # Create tables
        create_tables()
        
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful: %s", result.scalar())
        
        # Create default admin user if it doesn't exist
        user = db.query(User).filter(User.email == "admin@example.com").first()
        if not user:
            admin_user = User(
                email="admin@example.com",
                hashed_password=get_password_hash(settings.ADMIN_DEFAULT_PASSWORD),
                full_name="Admin User",
                is_superuser=True,
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            logger.info("Created default admin user")
        else:
            logger.info("Database already initialized with admin user")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        db.rollback()
