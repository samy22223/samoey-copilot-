import logging
from sqlalchemy.orm import Session
from backend.core.security import get_password_hash
from backend.models.user import User

logger = logging.getLogger(__name__)

async def init_db(db: Session) -> None:
    ""
    Initialize the database with default data.
    """
    # Create default admin user if it doesn't exist
    user = db.query(User).filter(User.email == "admin@example.com").first()
    if not user:
        try:
            admin_user = User(
                email="admin@example.com",
                hashed_password=get_password_hash("admin"),
                full_name="Admin User",
                is_superuser=True,
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            logger.info("Created default admin user")
        except Exception as e:
            logger.error(f"Error creating default admin user: {e}")
            db.rollback()
    else:
        logger.info("Database already initialized with admin user")
