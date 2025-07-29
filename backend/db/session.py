from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from backend.core.config import settings

# Create database engine
engine = create_engine(
    str(settings.DATABASE_URI),
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Scoped session for thread safety
ScopedSession = scoped_session(SessionLocal)

def get_db():
    """Dependency for getting database session"""
    db = ScopedSession()
    try:
        yield db
    finally:
        db.close()

def init_db():
    ""
    Initialize database tables
    This should be called during application startup
    ""
    from backend.models.base import Base
    from backend.models.user import User
    from backend.models.conversation import Conversation
    from backend.models.message import Message
    
    Base.metadata.create_all(bind=engine)
    
    # Create default admin user if not exists
    db = next(get_db())
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            from backend.core.security import get_password_hash
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin"),
                is_superuser=True,
                full_name="Admin User"
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
